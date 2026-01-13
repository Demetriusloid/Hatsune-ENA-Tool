import re
import tkinter as tk
import threading
from tkinter import Toplevel, ttk, Menu
from datetime import datetime
from ..gui.windows import FindReplaceDialog
from ..logic.backend import MT_AVAILABLE

class EditorController:
    """
    Controlador responsável pela área de edição (lado direito da interface).
    Gerencia a exibição de textos, validação em tempo real, tradução automática,
    histórico de edições e ferramentas de busca/substituição.
    """
    
    def __init__(self, app):
        self.app = app  # Referência à classe principal (ENATranslationTool)
        
        # Variáveis de estado para busca e substituição
        self.find_dialog = None
        self.last_search_idx = -1
        
        # Variáveis para o sistema de sugestão (Tooltip) ao passar o mouse
        self.tooltip = None
        self.hover_sug = None

    def on_select(self, event):
        """
        Chamado quando o usuário clica em uma linha na lista (Treeview).
        Carrega os dados da linha selecionada para os editores.
        """
        sel = self.app.tree.selection()
        if not sel: return

        # 1. Salva um snapshot da linha ANTERIOR no histórico antes de mudar
        if self.app.last_selected_id is not None: 
            self._add_history_snapshot(self.app.last_selected_id)
        
        # 2. Identifica a nova linha selecionada
        idx = int(sel[0])
        self.app.current_index = idx
        self.app.last_selected_id = idx
        data = self.app.translations[idx]
        
        # 3. Atualiza o cabeçalho (mostra de qual arquivo veio a tradução, se importada)
        source_text = f"Sua Tradução ({data.get('source_file','')})" if data.get('source_file') else "Sua Tradução"
        self.app.lbl_trans.config(text=source_text)
        
        # 4. Atualiza o checkbox "Perdoar Erros" com o estado salvo
        self.app.var_ignore_error.set(data.get("ignore_errors", False))
        
        # 5. Preenche a caixa de Texto Original (somente leitura)
        self.app.txt_original.config(state="normal")
        self.app.txt_original.delete("1.0", "end")
        self.app.txt_original.insert("1.0", data["original"])
        self.app.txt_original.config(state="disabled")
        
        # 6. Preenche a caixa de Tradução (editável)
        self.app.txt_translation.delete("1.0", "end")
        self.app.txt_translation.insert("1.0", data["translated"])
        self.app.txt_translation.edit_reset() # Reseta a pilha de undo/redo do Tkinter
        
        # 7. Mostra ou esconde o botão de histórico se houver versões anteriores
        if len(data.get("history", [])) > 1:
            self.app.btn_history.pack(side="left", padx=10)
        else:
            self.app.btn_history.pack_forget()
            
        # 8. Busca tradução automática se o painel estiver aberto
        if self.app.show_mt.get(): 
            self.fetch_mt_translation()
            
        # 9. Aplica cores (sintaxe) e verifica erros
        self.highlight_syntax()
        self.check_line_status()

    def on_edit_text(self, event):
        """
        Chamado a cada tecla digitada na caixa de tradução.
        Salva o texto na memória e atualiza validações em tempo real.
        """
        if self.app.current_index is None: return
        
        # Pega todo o texto da caixa (o -1c remove o \n automático final do Tkinter)
        txt = self.app.txt_translation.get("1.0", "end-1c")
        
        # Se houve mudança real, marca o projeto como "Não Salvo" (*)
        if self.app.translations[self.app.current_index]["translated"] != txt: 
            self.app.mark_unsaved()
            
        # Atualiza o dicionário de dados principal
        self.app.translations[self.app.current_index]["translated"] = txt
        
        # Revalida sintaxe e erros
        self.highlight_syntax()
        self.check_line_status()
        
        # Atualiza o ícone na árvore lateral (ex: mudar para lápis verde)
        self.update_tree_row(self.app.current_index)

    def update_tree_row(self, idx):
        """
        Atualiza visualmente apenas uma linha específica na árvore lateral.
        Evita ter que recarregar toda a lista (populate_tree) para ganhar performance.
        """
        tags = self.app.tree_ctrl.get_row_tags(idx)
        text = self.app.translations[idx]["translated"]
        
        # Cria um preview limpo (sem tags HTML)
        clean = re.sub(r'<.*?>', '', text)[:60]
        
        is_mod = 'modified' in tags
        disp = f"✎ {clean}" if is_mod else clean
        if 'mt_match' in tags: disp = f"🤖 {clean}"
        
        # Define o ícone de status
        icon = ""
        if 'alert' in tags: icon = "⚠️"
        elif 'glossary_issue' in tags: icon = "📖"
        
        # Aplica na árvore
        self.app.tree.item(idx, values=(idx, disp, icon), tags=tags)

    def highlight_syntax(self):
        """
        Aplica cores (tags do Text widget) em elementos especiais como HTML e keywords.
        """
        # Limpa formatações anteriores
        self.app.txt_translation.tag_remove("tag_xml", "1.0", "end")
        self.app.txt_translation.tag_remove("tag_ena", "1.0", "end")
        
        if not self.app.show_tags.get(): return
        
        txt = self.app.txt_translation.get("1.0", "end")
        
        # Colore tags HTML/XML (ex: <br>, <b>)
        for m in re.finditer(r'<[^>]+>', txt):
            self.app.txt_translation.tag_add("tag_xml", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        
        # Colore palavras reservadas do jogo
        for m in re.finditer(r'\b(ENASales|ENAMean|Whisper|Hint)\b', txt):
             self.app.txt_translation.tag_add("tag_ena", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def check_line_status(self):
        """
        Validação principal. Verifica Glossário, Tags, Ortografia e Gramática.
        Controla o sublinhado vermelho e a mensagem de alerta.
        """
        # Reseta alertas
        self.app.lbl_tag_alert.config(text="")
        self.app.lbl_tag_alert.pack_forget()
        
        # Limpa sublinhados de erro
        for t in ["misspelled", "grammar_error", "tag_error", "glossary_case_error"]: 
            self.app.txt_translation.tag_remove(t, "1.0", "end")

        # Se não há seleção ou se o usuário "Perdoou" a linha, não valida
        if self.app.current_index is None or self.app.var_ignore_error.get(): return
        
        data = self.app.translations[self.app.current_index]
        orig, text = data["original"], data["translated"]
        
        # 1. Validação de Glossário (Prioridade Alta)
        errs = self.app.audit_manager.validate_glossary(orig, text)
        msg_show = ""
        color_show = ""
        
        if errs: 
            msg_show = errs[0]
            color_show = self.app.current_theme.get("glossary_warn", "orange")
        
        # 2. Validação de Tags HTML (Prioridade Alta)
        elif self.app.show_tags.get():
            msg, k = self.app.audit_manager.validate_tags(orig, text)
            if k != "tag_ok": 
                msg_show = msg
                color_show = self.app.current_theme.get("tag_err", "red") if k == "tag_err" else "orange"

        # Exibe mensagem de alerta acima da caixa de texto se houver erro crítico
        if msg_show:
            self.app.lbl_tag_alert.config(text=msg_show, fg=color_show)
            self.app.lbl_tag_alert.pack(anchor="w", pady=(0, 2), before=self.app.txt_translation)

        # 3. Validação Ortográfica (Sublinhado)
        if self.app.show_spell.get():
            # Cria lista de intervalos protegidos (tags HTML) para não corrigir código
            protected = [(m.start(), m.end()) for m in re.finditer(r'<[^>]+>', text)]
            
            unks = self.app.audit_manager.check_spelling(text)
            if unks:
                for w in unks:
                    # Encontra todas as ocorrências da palavra errada
                    for m in re.finditer(r'\b'+re.escape(w)+r'\b', text):
                        s, e = m.start(), m.end()
                        # Só marca se não estiver dentro de uma tag HTML
                        if not any(ps <= s and e <= pe for ps, pe in protected):
                            self.app.txt_translation.tag_add("misspelled", f"1.0+{s}c", f"1.0+{e}c")

        # 4. Validação Gramatical (Espaços e Pontuação)
        if self.app.show_grammar.get():
             # Espaços duplos
             for m in re.finditer(r' {2,}', text):
                 self.app.txt_translation.tag_add("grammar_error", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
             # Pontuação sem espaço depois (ex: Olá.Tudo bem)
             for m in re.finditer(r'[\.,;:\?!](?!\s|$|\d|\.)\w', text):
                 self.app.txt_translation.tag_add("grammar_error", f"1.0+{m.start()}c", f"1.0+{m.end()+1}c")

    def has_errors(self, text, orig):
        """Helper simples que retorna True se a linha tem qualquer tipo de erro."""
        return (self.app.audit_manager.validate_glossary(orig, text) or 
                (self.app.show_tags.get() and self.app.audit_manager.validate_tags(orig, text)[1] != "tag_ok") or
                (self.app.show_spell.get() and self.app.audit_manager.check_spelling(text)) or
                (self.app.show_grammar.get() and self.app.audit_manager.check_grammar_issues(text, orig)))

    def fetch_mt_translation(self):
        """Inicia a tradução automática em uma thread separada (background)."""
        if not MT_AVAILABLE or not self.app.show_mt.get(): return
        if self.app.current_index is None: return
        
        # Limpa tags para enviar apenas o texto puro para o Google
        orig = re.sub(r'<[^>]+>', '', self.app.translations[self.app.current_index]["original"])
        
        def task():
            try: res = self.app.translator_service.translate(orig)
            except Exception as e: res = f"Erro: {str(e)}"
            # Agenda a atualização da UI para a thread principal
            self.app.root.after(0, lambda: self._update_mt_box(res))
            
        self._update_mt_box("Traduzindo...")
        threading.Thread(target=task, daemon=True).start()

    def _update_mt_box(self, text):
        """Atualiza a caixa de texto do tradutor (Machine Translation)."""
        self.app.txt_mt.config(state="normal")
        self.app.txt_mt.delete("1.0", "end")
        self.app.txt_mt.insert("1.0", text)
        self.app.txt_mt.config(state="disabled")
        
        # Salva em cache para o Modo Espião não precisar traduzir de novo
        if self.app.current_index is not None and "Traduzindo..." not in text and not text.startswith("Erro"): 
            self.app.translations[self.app.current_index]["mt_cache"] = text.strip()

    def toggle_mt_view(self):
        """
        Reconstrói o layout do lado direito para mostrar ou esconder a caixa do tradutor.
        Necessário usar pack_forget e pack novamente para manter a ordem correta.
        """
        # Remove tudo
        self.app.lbl_mt_header.pack_forget()
        self.app.txt_mt.pack_forget()
        self.app.header_frame.pack_forget()
        self.app.lbl_tag_alert.pack_forget()
        self.app.txt_translation.pack_forget()

        # Adiciona Tradutor (se ativo)
        if self.app.show_mt.get(): 
            self.app.lbl_mt_header.pack(anchor="w", pady=(0, 2))
            self.app.txt_mt.pack(fill="x", pady=(0, 10))
            if self.app.current_index is not None:
                self.fetch_mt_translation()
        
        # Adiciona Header da Tradução
        self.app.header_frame.pack(anchor="w", fill="x", pady=(10, 0))
        
        # Adiciona Alerta (se houver erro)
        if self.app.lbl_tag_alert.cget("text"):
            self.app.lbl_tag_alert.pack(anchor="w", pady=(2, 0))

        # Adiciona Caixa de Edição Principal
        self.app.txt_translation.pack(fill="both", expand=True, pady=(0, 0))

    def _add_history_snapshot(self, idx, global_log=True):
        """
        Salva o estado atual do texto no histórico local (da linha) e global (da sessão).
        """
        if idx not in self.app.translations: return
        curr = self.app.translations[idx]["translated"]
        
        # Evita salvar placeholders de loading
        if curr.strip().lower().startswith("line:"): return

        hist = self.app.translations[idx].get("history", [])
        
        # Só salva se o texto mudou em relação ao último snapshot
        if not hist or hist[-1]["text"] != curr:
            t = datetime.now().strftime("%H:%M:%S")
            hist.append({"time": t, "text": curr})
            self.app.translations[idx]["history"] = hist
            
            if global_log and len(hist) > 1: 
                self.app.session_log.append({"time": t, "id": idx, "text": curr})
            
            # Limita histórico por linha para economizar memória
            if len(hist) > 50: hist.pop(0)

    def open_history_window(self):
        """Abre janela para ver versões anteriores da linha atual."""
        if self.app.current_index is None: return
        win = Toplevel(self.app.root)
        win.title(f"Histórico ID {self.app.current_index}")
        win.geometry("400x300")
        
        tree = ttk.Treeview(win, columns=("t", "txt"), show="headings")
        tree.heading("t", text="Hora"); tree.column("t", width=80)
        tree.heading("txt", text="Texto"); tree.column("txt", width=300)
        tree.pack(fill="both", expand=True)
        
        hist = self.app.translations[self.app.current_index].get("history", [])
        for h in reversed(hist):
            tree.insert("", "end", values=(h["time"], h["text"]))
            
        def restore():
            sel = tree.selection()
            if not sel: return
            val = tree.item(sel[0])["values"][1]
            # Restaura o texto antigo
            self.app.txt_translation.delete("1.0", "end")
            self.app.txt_translation.insert("1.0", val)
            self.on_edit_text(None) # Dispara evento de edição para salvar
            win.destroy()
            
        ttk.Button(win, text="Restaurar Selecionado", command=restore).pack(pady=5)

    def show_session_log_window(self):
        """Abre janela com o log de todas as alterações feitas na sessão."""
        win = Toplevel(self.app.root); win.title("Log Global")
        win.geometry("600x400")
        tree = ttk.Treeview(win, columns=("t", "id", "txt"), show="headings")
        tree.heading("t", text="Hora"); tree.column("t", width=80)
        tree.heading("id", text="ID"); tree.column("id", width=50)
        tree.heading("txt", text="Texto"); tree.column("txt", width=400)
        tree.pack(fill="both", expand=True)
        
        for l in reversed(self.app.session_log): 
            tree.insert("", "end", values=(l["time"], l["id"], l["text"]))

    def show_advanced_find(self):
        """Abre a janela de Localizar/Substituir."""
        if not self.app.translations: return
        if self.find_dialog and self.find_dialog.win.winfo_exists():
            self.find_dialog.win.lift()
        else:
            self.find_dialog = FindReplaceDialog(self.app.root, self, self.app.current_theme)

    def find_next_action(self, v_find, v_case, v_whole):
        """Lógica do botão 'Localizar Próximo'."""
        pat_str = v_find.get()
        if not pat_str: return
        
        flags = 0 if v_case.get() else re.IGNORECASE
        pattern = re.escape(pat_str)
        if v_whole.get(): pattern = r'\b' + pattern + r'\b'
        
        try: regex = re.compile(pattern, flags)
        except: return

        keys = list(self.app.translations.keys())
        # Começa a busca logo após o índice atual
        start = self.last_search_idx + 1
        # Cria uma lista circular (do atual até o fim, depois do inicio até o atual)
        order = keys[start:] + keys[:start]
        
        found = None
        for idx in order:
            if regex.search(self.app.translations[idx]["translated"]):
                found = idx
                break
        
        if found is not None:
            self.last_search_idx = found
            self.app.tree.selection_set(found)
            self.app.tree.see(found)
            self.on_select(None)
            
            # Seleciona o texto encontrado na caixa de edição
            txt = self.app.translations[found]["translated"]
            m = regex.search(txt)
            if m:
                self.app.txt_translation.tag_remove("sel", "1.0", "end")
                self.app.txt_translation.tag_add("sel", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
                self.app.txt_translation.focus_set()

    def replace_current(self, f, r, c, w):
        """Substitui a ocorrência na linha atual."""
        if self.app.current_index is None: return
        curr = self.app.translations[self.app.current_index]["translated"]
        
        pat_str = f.get()
        if not pat_str: return
        
        flags = 0 if c.get() else re.IGNORECASE
        pattern = re.escape(pat_str)
        if w.get(): pattern = r'\b' + pattern + r'\b'
        
        new_t = re.sub(pattern, r.get(), curr, count=1, flags=flags)
        
        if new_t != curr:
            self.app.txt_translation.delete("1.0", "end")
            self.app.txt_translation.insert("1.0", new_t)
            self.on_edit_text(None)

    def replace_all(self, f, r, c, w):
        """Substitui todas as ocorrências em TODAS as linhas."""
        pat_str = f.get()
        if not pat_str: return
        
        flags = 0 if c.get() else re.IGNORECASE
        pattern = re.escape(pat_str)
        if w.get(): pattern = r'\b' + pattern + r'\b'
        regex = re.compile(pattern, flags)
        
        cnt = 0
        for k, v in self.app.translations.items():
            new_t = regex.sub(r.get(), v["translated"])
            if new_t != v["translated"]:
                self.app.translations[k]["translated"] = new_t
                self._add_history_snapshot(k) # Salva histórico antes de alterar
                cnt += 1
        
        if cnt:
            self.app.tree_ctrl.populate_tree() # Atualiza a lista visual
            if self.app.current_index is not None: self.on_select(None) # Recarrega linha atual
            self.app.mark_unsaved()
            tk.messagebox.showinfo("Substituir Tudo", f"{cnt} ocorrências substituídas.")

    def on_text_motion(self, event):
        """
        Detecta se o mouse está sobre uma palavra marcada como erro ortográfico.
        Se sim, mostra um tooltip com a sugestão.
        """
        if not self.app.show_spell.get(): return
        try:
            # Obtém o índice do caractere sob o mouse
            idx = self.app.txt_translation.index(f"@{event.x},{event.y}")
            tags = self.app.txt_translation.tag_names(idx)
            
            if "misspelled" in tags and self.app.audit_manager.spell:
                word = self.app.txt_translation.get(idx + " wordstart", idx + " wordend")
                cands = self.app.audit_manager.spell.candidates(word)
                if cands:
                    cand = list(cands)[0]
                    self.show_tooltip(f"Sugestão: {cand} (TAB)", event.x_root, event.y_root)
                    self.hover_sug = (idx + " wordstart", idx + " wordend", cand)
                    return
        except: pass
        self.hide_tooltip()

    def show_tooltip(self, text, x, y):
        """Exibe uma pequena janela flutuante com texto."""
        if self.tooltip: self.tooltip.destroy()
        self.tooltip = Toplevel(self.app.root)
        self.tooltip.wm_overrideredirect(True) # Remove borda da janela
        self.tooltip.geometry(f"+{x+10}+{y+10}")
        tk.Label(self.tooltip, text=text, bg="#333", fg="#fff", padx=5, pady=2, relief="solid", bd=1).pack()

    def hide_tooltip(self, e=None):
        if self.tooltip: self.tooltip.destroy(); self.tooltip = None
        self.hover_sug = None

    def on_tab_pressed(self, event):
        """Se houver uma sugestão de correção ativa (hover), a tecla TAB aplica a correção."""
        if self.hover_sug:
            s, e, r = self.hover_sug
            self.app.txt_translation.delete(s, e)
            self.app.txt_translation.insert(s, r)
            self.on_edit_text(None)
            self.hide_tooltip()
            return "break" # Impede o TAB de inserir espaço

    def add_undo_separator(self, event): 
        """Adiciona um marco no sistema de Undo/Redo do Tkinter (ex: ao dar espaço)."""
        self.app.txt_translation.edit_separator()
    
    def show_context_menu(self, event):
        """Menu de clique direito com sugestões de correção e 'Adicionar ao Dicionário'."""
        try:
            idx = self.app.txt_translation.index(f"@{event.x},{event.y}")
            word = self.app.txt_translation.get(idx + " wordstart", idx + " wordend")
            
            m = Menu(self.app.root, tearoff=0)
            
            if self.app.show_spell.get() and self.app.audit_manager.spell:
                cands = self.app.audit_manager.spell.candidates(word)
                if cands:
                    # Adiciona as 5 melhores sugestões
                    for c in list(cands)[:5]:
                        m.add_command(label=c, command=lambda val=c: self._apply_fix(val, idx))
                    m.add_separator()
            
            m.add_command(label="Adicionar ao Dicionário", command=lambda: self.add_to_dict(word))
            m.tk_popup(event.x_root, event.y_root)
        except: pass

    def _apply_fix(self, val, idx):
        """Aplica a correção selecionada no menu de contexto."""
        ws = idx + " wordstart"
        we = idx + " wordend"
        self.app.txt_translation.delete(ws, we)
        self.app.txt_translation.insert(ws, val)
        self.on_edit_text(None)

    def add_to_dict(self, word):
        """Adiciona a palavra ao dicionário em memória para parar de marcar como erro."""
        if self.app.audit_manager.spell:
            self.app.audit_manager.spell.word_frequency.load_words([word])
            self.refresh_audit_view()

    def refresh_audit_view(self):
        """Força a re-verificação de erros na linha atual e na árvore."""
        self.check_line_status()
        self.app.tree_ctrl.populate_tree()

    def on_toggle_ignore(self):
        """Chamado quando o usuário clica no checkbox 'Ignorar Erros'."""
        if self.app.current_index is not None:
            self.app.translations[self.app.current_index]["ignore_errors"] = self.app.var_ignore_error.get()
            self.check_line_status()
            self.update_tree_row(self.app.current_index)

    def focus_search(self, event=None):
        """Atalho CTRL+F: Foca na caixa de busca da lista lateral."""
        self.app.entry_search.focus_set()
        self.app.entry_search.select_range(0, tk.END)