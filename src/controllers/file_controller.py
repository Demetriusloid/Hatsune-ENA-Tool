import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, Entry, Button, Frame, ttk
from ..logic.backend import FileManager

class FileController:
    def __init__(self, app):
        self.app = app

    def load_base_file(self):
        if self.app.translations and self.app.unsaved_changes:
            ans = messagebox.askyesnocancel("Fechar Trabalho", "Salvar sessão antes de carregar nova base?")
            if ans is None: return
            if ans: self.app.save_auto_session()

        filename = filedialog.askopenfilename(title="Arquivo ORIGINAL (EN)", filetypes=[("Text Files", "*.txt")])
        if not filename: return

        try:
            with open(filename, 'r', encoding='utf-8') as f: lines = f.readlines()
            new_parsed = FileManager.parse_file_to_dict(lines)
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo:\n{str(e)}"); return

        keep = False
        if self.app.translations:
            ans = messagebox.askyesnocancel("Nova Base", "Manter traduções atuais?")
            if ans is None: return
            keep = ans

        self.app.base_filepath = filename
        self.app.base_lines = lines
        new_dict = {}
        for idx, item in new_parsed.items():
            entry = {"original": item["text"], "translated": item["text"], "has_quotes": item["quotes"], 
                     "mt_cache": None, "original_line": item["original_line"], 
                     "history": [{"time": "Original", "text": item["text"]}], "source_file": None, "ignore_errors": False}
            if keep and idx in self.app.translations:
                old = self.app.translations[idx]
                entry.update({"translated": old["translated"], "history": old.get("history", []), 
                              "source_file": old.get("source_file"), "ignore_errors": old.get("ignore_errors", False), 
                              "mt_cache": old.get("mt_cache")})
            new_dict[idx] = entry
        
        self.app.translations = new_dict
        self.app.tree_ctrl.populate_tree()
        self.app.lbl_status.config(text=f"Base: {len(new_dict)} linhas")
        self.app.lbl_orig.config(text=f"Original: {os.path.basename(filename)}")
        for b in [self.app.btn_import_trans, self.app.btn_import_partial, self.app.btn_export_mod]: b.config(state="normal")
        if keep: self.app.mark_unsaved()
        else: self.app.mark_saved()

    def save_file(self, event=None):
        if not self.app.base_lines: return
        if self.app.current_index is not None: self.app.editor_ctrl._add_history_snapshot(self.app.current_index)
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", title="Salvar Arquivo")
        if not save_path: return
        try:
            new_lines = self.app.base_lines[:]
            pat = re.compile(r'^(.*1 string data = )(.*)$')
            for idx, data in self.app.translations.items():
                line_idx = data["original_line"]
                if line_idx < len(new_lines):
                    m = pat.match(new_lines[line_idx])
                    if m:
                        content = f'"{data["translated"]}"' if data["has_quotes"] else data["translated"]
                        new_lines[line_idx] = m.group(1) + content + "\n"
            with open(save_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)
            self.app.mark_saved()
            messagebox.showinfo("Sucesso", "Arquivo salvo!")
        except Exception as e: messagebox.showerror("Erro", str(e))

    def import_translation_file(self):
        if not self.app.translations: return
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not filename: return
        try:
            with open(filename, 'r', encoding='utf-8') as f: lines = f.readlines()
            updates = {}
            has_ids = any(re.match(r'^\s*\[(\d+)\]', l) for l in lines)
            if has_ids:
                curr = -1
                for l in lines:
                    m = re.match(r'^\s*\[(\d+)\]', l)
                    if m: curr = int(m.group(1)); continue
                    if curr != -1:
                        m2 = re.match(r'^\s*1 string data = (.*)$', l)
                        if m2:
                            raw = m2.group(1).strip()
                            updates[curr] = raw[1:-1] if (len(raw)>=2 and raw.startswith('"') and raw.endswith('"')) else raw
                            curr = -1
            else:
                parsed = FileManager.parse_file_to_dict(lines)
                for k, v in parsed.items(): updates[k] = v["text"]
            self._process_updates(updates, os.path.basename(filename))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def import_partial_file(self):
        filename = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not filename: return
        rng = self._ask_range()
        if not rng: return
        mn, mx = rng
        try:
            with open(filename, 'r', encoding='utf-8') as f: lines = f.readlines()
            updates = {}
            curr = -1
            for l in lines:
                m = re.match(r'^\s*\[(\d+)\]', l)
                if m: curr = int(m.group(1)); continue
                if curr != -1 and mn <= curr <= mx:
                    m2 = re.match(r'^\s*1 string data = (.*)$', l)
                    if m2:
                        raw = m2.group(1).strip()
                        updates[curr] = raw[1:-1] if (len(raw)>=2 and raw.startswith('"') and raw.endswith('"')) else raw
                        curr = -1
            self._process_updates(updates, os.path.basename(filename))
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _process_updates(self, updates, source):
        if not updates: return
        cnt = 0
        for k, v in updates.items():
            if k in self.app.translations:
                if self.app.translations[k]["translated"] != v:
                    self.app.translations[k]["translated"] = v
                    self.app.translations[k]["source_file"] = source
                    self.app.editor_ctrl._add_history_snapshot(k, False)
                    cnt += 1
        self.app.tree_ctrl.populate_tree()
        if cnt: self.app.mark_unsaved()
        messagebox.showinfo("Importação", f"{cnt} linhas atualizadas.")

    def _ask_range(self):
        c = self.app.current_theme
        win = Toplevel(self.app.root); win.title("Intervalo"); win.geometry("300x150")
        win.configure(bg=c["bg_ribbon"])
        win.transient(self.app.root)
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() // 2) - 150
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() // 2) - 75
        win.geometry(f"+{x}+{y}")

        Label(win, text="IDs para importar:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(pady=10)
        f = Frame(win, bg=c["bg_ribbon"]); f.pack()
        Label(f, text="De:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side="left")
        e1 = Entry(f, width=8); e1.pack(side="left", padx=5)
        Label(f, text="Até:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side="left")
        e2 = Entry(f, width=8); e2.pack(side="left", padx=5)
        res = []
        def ok():
            try: res.extend([int(e1.get()), int(e2.get())]); win.destroy()
            except: messagebox.showerror("Erro", "Apenas números.")
        Button(win, text="Confirmar", command=ok, bg=c["accent"], fg="white").pack(pady=15)
        self.app.root.wait_window(win)
        return tuple(res) if res else None

    def unload_all_files(self):
        if not messagebox.askyesno("Reset", "Zerar tudo? Isso apagará o histórico da sessão atual."): return
        self.app.base_filepath = ""
        self.app.base_lines = []
        self.app.translations = {}
        self.app.current_index = None
        self.app.session_log = []
        self.app.audit_manager.glossary = {}
        self.app.baseline_snapshot = {}
        self.app.unsaved_changes = False
        self.app.use_custom_baseline.set(False)
        self.app.spy_mode = False
        
        self.app.tree.delete(*self.app.tree.get_children())
        self.app.txt_original.config(state="normal"); self.app.txt_original.delete("1.0", "end"); self.app.txt_original.config(state="disabled")
        self.app.txt_translation.delete("1.0", "end")
        self.app.txt_mt.config(state="normal"); self.app.txt_mt.delete("1.0", "end"); self.app.txt_mt.config(state="disabled")
        
        self.app.lbl_status.config(text="")
        self.app.lbl_orig.config(text="Texto Original (Inglês):")
        self.app.lbl_trans.config(text="Sua Tradução")
        self.app.btn_history.pack_forget()
        
        for b in [self.app.btn_import_trans, self.app.btn_import_partial, self.app.btn_export_mod]: b.config(state="disabled")
        if os.path.exists(self.app.SESSION_FILE): 
            try: os.remove(self.app.SESSION_FILE)
            except: pass
        messagebox.showinfo("Reset Concluído", "O aplicativo foi resetado com sucesso.")

    def open_export_selector(self):
        if not self.app.translations:
            messagebox.showwarning("Aviso", "Nada para exportar.")
            return

        c = self.app.current_theme
        win = Toplevel(self.app.root)
        win.title("Exportar Linhas Selecionadas")
        win.geometry("1000x700") 
        win.configure(bg=c["bg_root"])
        win.transient(self.app.root)
        
        var_search_text = tk.StringVar()
        var_filter_mod = tk.BooleanVar(value=False)
        var_filter_alert = tk.BooleanVar(value=False)

        top_bar = Frame(win, bg=c["bg_ribbon"], pady=10, padx=10)
        top_bar.pack(fill=tk.X)
        
        # Pesquisa
        search_frame = Frame(top_bar, bg=c["bg_ribbon"])
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        Label(search_frame, text="🔍 Pesquisar:", bg=c["bg_ribbon"], fg=c["fg_text"], font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        entry_search_export = Entry(search_frame, textvariable=var_search_text, bg=c["bg_editor"], fg=c["fg_text"], insertbackground=c["cursor"])
        entry_search_export.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Filtros
        filter_frame = Frame(top_bar, bg=c["bg_ribbon"])
        filter_frame.pack(side=tk.LEFT, padx=10)
        
        # Lista
        list_frame = Frame(win, bg=c["bg_list"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cols = ("id", "text", "status")
        tree_sel = ttk.Treeview(list_frame, columns=cols, show="headings", selectmode="extended")
        tree_sel.heading("id", text="ID"); tree_sel.heading("text", text="Texto"); tree_sel.heading("status", text="Alertas")
        tree_sel.column("id", width=60, anchor="center", stretch=False); tree_sel.column("text", width=650); tree_sel.column("status", width=60, anchor="center", stretch=False)
        sb = tk.Scrollbar(list_frame, orient="vertical", command=tree_sel.yview)
        tree_sel.configure(yscroll=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree_sel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_sel.tag_configure('modified', foreground=c["modified_item"]) 
        tree_sel.tag_configure('alert', foreground=c["alert_icon"]) 
        tree_sel.tag_configure('glossary_issue', foreground=c["glossary_warn"])

        def populate_export_list(event=None):
            tree_sel.delete(*tree_sel.get_children())
            search_term = var_search_text.get().lower()
            filter_mod_only = var_filter_mod.get()
            filter_alert_only = var_filter_alert.get()

            for idx in sorted(self.app.translations.keys()):
                data = self.app.translations[idx]
                text, orig = data["translated"], data["original"]
                
                if search_term and (search_term not in text.lower() and search_term not in orig.lower()): continue
                
                tags = []
                is_modified = False
                if self.app.use_custom_baseline.get():
                    baseline_text = self.app.baseline_snapshot.get(idx, orig)
                    if text != baseline_text: is_modified = True
                else:
                    if text != orig: is_modified = True
                if is_modified: tags.append('modified')

                has_alert = False
                if not data.get("ignore_errors", False):
                    if self.app.audit_manager.validate_glossary(orig, text): 
                        tags.append('glossary_issue'); has_alert = True
                    elif self.app.editor_ctrl.has_errors(text, orig): 
                        tags.append('alert'); has_alert = True

                if filter_mod_only and not is_modified: continue
                if filter_alert_only and not has_alert: continue

                clean_preview = re.sub(r'<.*?>', '', text)[:90]
                display_text = "✎ " + clean_preview if is_modified else clean_preview
                icon = "📖" if 'glossary_issue' in tags else ("⚠️" if 'alert' in tags else "")
                tree_sel.insert("", "end", iid=str(idx), values=(idx, display_text, icon), tags=tuple(tags))

        # Checkbuttons usando command em vez de trace
        tk.Checkbutton(filter_frame, text="Apenas Modificados", variable=var_filter_mod, command=populate_export_list, 
                       bg=c["bg_ribbon"], fg=c["modified_item"], selectcolor=c["bg_ribbon"]).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(filter_frame, text="Apenas Alertas", variable=var_filter_alert, command=populate_export_list, 
                       bg=c["bg_ribbon"], fg=c["alert_icon"], selectcolor=c["bg_ribbon"]).pack(side=tk.LEFT, padx=5)

        entry_search_export.bind("<KeyRelease>", populate_export_list)
        
        # Ir para ID
        goto_frame = Frame(top_bar, bg=c["bg_ribbon"])
        goto_frame.pack(side=tk.RIGHT)
        Label(goto_frame, text="Ir p/ ID:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side=tk.LEFT)
        entry_goto = Entry(goto_frame, width=6, bg=c["bg_editor"], fg=c["fg_text"], insertbackground=c["cursor"])
        entry_goto.pack(side=tk.LEFT, padx=5)
        
        def go_to_id(event=None):
            target = entry_goto.get().strip()
            if not target: return
            if tree_sel.exists(target):
                tree_sel.see(target); tree_sel.selection_set(target); tree_sel.focus(target)      
            else: messagebox.showwarning("Busca", f"ID {target} não encontrado.", parent=win)
        entry_goto.bind("<Return>", go_to_id)
        Button(goto_frame, text="➜", command=go_to_id, bg=c["btn_subtle"], fg=c["fg_text"], relief="raised", bd=1).pack(side=tk.LEFT)

        populate_export_list()

        # Drag Select
        def on_drag_select(event):
            row_id = tree_sel.identify_row(event.y)
            if row_id and row_id not in tree_sel.selection():
                current = list(tree_sel.selection()); current.append(row_id); tree_sel.selection_set(current)
        tree_sel.bind("<B1-Motion>", on_drag_select)

        # Footer
        footer = Frame(win, bg=c["bg_root"], pady=10)
        footer.pack(fill=tk.X)
        
        def select_visible_modified():
            sel = list(tree_sel.selection())
            for item in tree_sel.get_children():
                if "modified" in tree_sel.item(item, "tags") and item not in sel: sel.append(item)
            tree_sel.selection_set(sel)
        
        def select_all_visible(): tree_sel.selection_set(tree_sel.get_children())

        btn_frame = Frame(footer, bg=c["bg_root"])
        btn_frame.pack(side=tk.TOP, pady=(0, 10))
        Button(btn_frame, text="Selecionar Todos Visíveis", command=select_all_visible, bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="Selecionar Apenas Verdes (Visíveis)", command=select_visible_modified, bg=c["accent"], fg="white").pack(side=tk.LEFT, padx=5)

        def do_export():
            sel = tree_sel.selection()
            if not sel: messagebox.showwarning("Aviso", "Nenhuma linha selecionada!", parent=win); return
            ids = sorted([int(x) for x in sel])
            self.perform_selection_export(ids)
            win.destroy()
        Button(footer, text=f"💾 EXPORTAR SELEÇÃO", command=do_export, bg=c["modified_item"], fg="white", font=("Segoe UI", 11, "bold")).pack(side=tk.BOTTOM)

    def perform_selection_export(self, ids_list):
        save_path = filedialog.asksaveasfilename(defaultextension=".txt", title=f"Exportar {len(ids_list)} Linhas", filetypes=[("Text Files", "*.txt")])
        if not save_path: return
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                for idx in ids_list:
                    if idx in self.app.translations:
                        data = self.app.translations[idx]
                        content = data["translated"]
                        if data["has_quotes"]: content = f'"{content}"'
                        f.write(f"[{idx}]\n")
                        f.write(f"\t1 string data = {content}\n\n")
            messagebox.showinfo("Sucesso", f"{len(ids_list)} linhas exportadas com sucesso!")
        except Exception as e: messagebox.showerror("Erro ao salvar", str(e))