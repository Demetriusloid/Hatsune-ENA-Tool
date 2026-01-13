import time
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, Toplevel, Label, Entry, Button, Frame
from ..gui.windows import ProgressPopup
from ..logic.backend import MT_AVAILABLE

class TreeController:
    def __init__(self, app):
        self.app = app
        self.spy_active = False
        self.prog_win = None
        self.filter_popup = None
        self.chk_widgets = {}

    def get_row_tags(self, idx):
        data = self.app.translations[idx]
        text, orig = data["translated"], data["original"]
        tags = []
        if not data.get("ignore_errors", False):
            if self.app.audit_manager.validate_glossary(orig, text): tags.append('glossary_issue')
            elif self.app.editor_ctrl.has_errors(text, orig): tags.append('alert')
        
        if self.app.spy_mode and data.get("mt_cache"):
            clean_t = re.sub(r'<[^>]+>', '', text).strip()
            clean_m = re.sub(r'<[^>]+>', '', data["mt_cache"]).strip()
            clean_o = re.sub(r'<[^>]+>', '', orig).strip()
            if clean_t == clean_m and clean_t != clean_o: tags.append('mt_match')

        base = self.app.baseline_snapshot.get(idx, orig) if self.app.use_custom_baseline.get() else orig
        if text != base: tags.append('modified')
        return tuple(tags)

    def populate_tree(self, query=None):
        for i in self.app.tree.get_children(): self.app.tree.delete(i)
        query = query.lower() if query else ""
        try: mn, mx = int(self.app.id_min_var.get() or 0), int(self.app.id_max_var.get() or 99999999)
        except: mn, mx = 0, 99999999
        
        count = 0
        for idx, data in self.app.translations.items():
            if idx < mn or idx > mx: continue
            text, orig = data["translated"], data["original"]
            if query and (query not in text.lower() and query not in orig.lower()): continue
            
            tags = self.get_row_tags(idx)
            is_mod = 'modified' in tags
            has_err = 'alert' in tags or 'glossary_issue' in tags
            
            # Filtros
            if self.app.filters["modified"] and not self.app.filters["original"] and not is_mod: continue
            elif self.app.filters["original"] and not self.app.filters["modified"] and is_mod: continue
            if self.app.filters["alerts"] and not has_err: continue
            if self.app.filters["tags"] and not (re.search(r'<[^>]+>', text) or re.search(r'<[^>]+>', orig)): continue
            if self.app.filters["glossary"] and 'glossary_issue' not in tags: continue
            if self.app.filters["mt_match"] and 'mt_match' not in tags: continue
            
            clean = re.sub(r'<.*?>', '', text)[:60]
            disp = f"✎ {clean}" if is_mod else clean
            if 'mt_match' in tags: disp = f"🤖 {clean}"
            icon = "📖" if 'glossary_issue' in tags else ("⚠️" if 'alert' in tags else "")
            
            self.app.tree.insert("", "end", iid=idx, values=(idx, disp, icon), tags=tags)
            count += 1; 
            if count > 2000 and not query and mn==0 and mx==99999999: break

    def filter_list(self, event): self.populate_tree(self.app.entry_search.get())

    def toggle_custom_baseline(self):
        if self.app.use_custom_baseline.get():
            self.app.baseline_snapshot = {k: v["translated"] for k, v in self.app.translations.items()}
            messagebox.showinfo("Zerar Verdes", "Visual resetado! Novas edições ficarão verdes.")
        else: 
            if not messagebox.askokcancel("Restaurar", "Isso fará linhas traduzidas ficarem verdes de novo."):
                self.app.use_custom_baseline.set(True); return
            self.app.baseline_snapshot = {}
        self.populate_tree()

    def toggle_spy_mode(self, event=None):
        self.app.spy_mode = not self.app.spy_mode
        if not self.app.spy_mode: self.app.filters["mt_match"] = False
        c = self.app.current_theme["mt_match"] if self.app.spy_mode else self.app.current_theme["audit_label"]
        self.app.lbl_audit.config(fg=c)
        messagebox.showinfo("Modo Espião 🕵️", f"Status: {'ATIVADO' if self.app.spy_mode else 'DESATIVADO'}")
        self.populate_tree()

    def run_spy_batch_scan(self):
        if not MT_AVAILABLE: messagebox.showerror("Erro", "Tradutor indisponível."); return
        try: s, e = int(self.app.spy_scan_min.get()), int(self.app.spy_scan_max.get())
        except: messagebox.showerror("Erro", "IDs inválidos."); return
        if s > e: messagebox.showerror("Erro", "Inicio > Fim."); return
        
        self.spy_active = True
        self.prog_win = ProgressPopup(self.app.root, self.app.current_theme, s, e, self.cancel_scan)
        threading.Thread(target=self._scan, args=(s, e), daemon=True).start()

    def _scan(self, s, e):
        total = e - s + 1
        cnt = 0
        for i in range(s, e + 1):
            if not self.spy_active: break
            if i in self.app.translations and not self.app.translations[i]["mt_cache"]:
                orig = re.sub(r'<[^>]+>', '', self.app.translations[i]["original"])
                try: 
                    if cnt > 0 and cnt % 20 == 0: time.sleep(0.5)
                    self.app.translations[i]["mt_cache"] = self.app.translator_service.translate(orig).strip()
                except: pass
            cnt += 1
            if self.prog_win: 
                self.app.root.after(0, lambda c=cnt: self.prog_win.update(i, c, total, 0, 0))
        self.app.root.after(0, self.populate_tree)
        if self.spy_active: 
            self.app.root.after(0, self.prog_win.destroy)
            self.app.root.after(0, lambda: messagebox.showinfo("Fim", "Scan concluído."))

    def cancel_scan(self):
        self.spy_active = False
        if self.prog_win: self.prog_win.destroy()

    def handle_tree_click(self, event):
        if self.app.tree.identify_region(event.x, event.y) != "cell": return
        if self.app.tree.identify_row(event.y) in self.app.tree.selection():
            self.app.tree.selection_remove(self.app.tree.identify_row(event.y)); return "break"

    def on_tree_hover(self, event):
        item = self.app.tree.identify_row(event.y)
        if item:
            tags = self.app.tree.item(item, "tags")
            if any(x in tags for x in ['alert', 'glossary_issue']):
                try:
                    real_id = int(item)
                    msg = self.app.tree_ctrl.get_error_detail(real_id)
                    if msg: self.app.editor_ctrl.show_tooltip(msg, event.x_root+15, event.y_root+10)
                except: pass
            else: self.app.editor_ctrl.hide_tooltip()
        else: self.app.editor_ctrl.hide_tooltip()

    def get_error_detail(self, idx):
        # Helper para tooltip
        if idx not in self.app.translations: return None
        data = self.app.translations[idx]
        t, o = data["translated"], data["original"]
        gloss = self.app.audit_manager.validate_glossary(o, t)
        if gloss: return "\n".join(gloss)
        if self.app.show_tags.get():
            msg, k = self.app.audit_manager.validate_tags(o, t)
            if k != "tag_ok": return f"Tag HTML: {msg}"
        return "Erro Genérico"

    def toggle_filter_popup(self, event):
        if self.filter_popup:
            self.filter_popup.destroy(); self.filter_popup = None; return
        
        c = self.app.current_theme
        self.filter_popup = Toplevel(self.app.root)
        self.filter_popup.wm_overrideredirect(True)
        self.filter_popup.configure(bg=c["border"])
        
        # Posicionamento
        btn = self.app.btn_filter
        x = btn.winfo_rootx() - 150
        y = btn.winfo_rooty() + btn.winfo_height() + 5
        self.filter_popup.geometry(f"250x100+{x}+{y}")
        
        inner = Frame(self.filter_popup, bg=c["bg_ribbon"], padx=15, pady=15)
        inner.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        Label(inner, text="FILTRAR POR STATUS", font=("Segoe UI", 9, "bold"), bg=c["bg_ribbon"], fg=c["fg_dim"]).pack(anchor="w", pady=(0, 10))
        
        grid = Frame(inner, bg=c["bg_ribbon"]); grid.pack(fill=tk.BOTH, expand=True)
        blocks = [("Modificados", "modified"), ("Originais", "original"), ("Com Alertas", "alerts"), ("Com Tags", "tags"), ("Erro Glossário", "glossary")]
        if self.app.spy_mode: blocks.append(("Tradutor", "mt_match"))
        
        self.chk_widgets = {}
        for i, (txt, key) in enumerate(blocks):
            row = Frame(grid, bg=c["bg_ribbon"], cursor="hand2", pady=5)
            row.grid(row=i, column=0, sticky="ew", pady=2)
            chk = Label(row, text="", font=("Segoe UI", 9, "bold"), width=3, height=1, relief="solid", borderwidth=1, cursor="hand2")
            chk.pack(side="left", padx=(0, 10))
            lbl = Label(row, text=txt, font=("Segoe UI", 10), bg=c["bg_ribbon"], fg=c["fg_text"], cursor="hand2")
            lbl.pack(side="left")
            
            self.chk_widgets[key] = chk
            self._update_chk_vis(key, chk)
            
            # Bindings
            cmd = lambda e, k=key, w=chk: self.toggle_filter_state(k, w)
            row.bind("<Button-1>", cmd); chk.bind("<Button-1>", cmd); lbl.bind("<Button-1>", cmd)

        Frame(inner, height=1, bg=c["border"]).pack(fill=tk.X, pady=10)
        
        Label(inner, text="INTERVALO (ID)", font=("Segoe UI", 9, "bold"), bg=c["bg_ribbon"], fg=c["fg_dim"]).pack(anchor="w")
        rf = Frame(inner, bg=c["bg_ribbon"], pady=5); rf.pack(fill=tk.X)
        Label(rf, text="De:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side="left")
        e1 = Entry(rf, textvariable=self.app.id_min_var, width=5, justify="center"); e1.pack(side="left", padx=5)
        e1.bind("<KeyRelease>", self.filter_list)
        Label(rf, text="Até:", bg=c["bg_ribbon"], fg=c["fg_text"]).pack(side="left")
        e2 = Entry(rf, textvariable=self.app.id_max_var, width=5, justify="center"); e2.pack(side="left", padx=5)
        e2.bind("<KeyRelease>", self.filter_list)

        if self.app.spy_mode:
            Frame(inner, height=1, bg=c["border"]).pack(fill=tk.X, pady=10)
            Label(inner, text="DETECTAR (BATCH)", font=("Segoe UI", 9, "bold"), bg=c["bg_ribbon"], fg=c["mt_match"]).pack(anchor="w")
            sf = Frame(inner, bg=c["bg_ribbon"], pady=5); sf.pack(fill=tk.X)
            Entry(sf, textvariable=self.app.spy_scan_min, width=5).pack(side="left", padx=5)
            Entry(sf, textvariable=self.app.spy_scan_max, width=5).pack(side="left", padx=5)
            Button(inner, text="🔍 Escanear", command=self.run_spy_batch_scan, bg=c["mt_match"], fg="white", relief="flat").pack(fill=tk.X, pady=5)

        Frame(inner, height=1, bg=c["border"]).pack(fill=tk.X, pady=10)
        rst = Label(inner, text="LIMPAR FILTROS", font=("Segoe UI", 8, "bold"), bg=c["bg_ribbon"], fg=c["error_spell"], cursor="hand2")
        rst.pack(pady=5); rst.bind("<Button-1>", self.reset_filters)
        
        self.filter_popup.update_idletasks()
        self.filter_popup.geometry(f"250x{inner.winfo_reqheight()+5}+{x}+{y}")

    def toggle_filter_state(self, key, widget):
        self.app.filters[key] = not self.app.filters[key]
        self._update_chk_vis(key, widget)
        self.populate_tree()

    def _update_chk_vis(self, key, widget):
        c = self.app.current_theme
        if self.app.filters[key]: widget.configure(bg=c["accent"], fg="white", text="✓", bd=0)
        else: widget.configure(bg=c["bg_ribbon"], fg=c["bg_ribbon"], text="", bd=1, relief="solid")

    def reset_filters(self, event):
        for k in self.app.filters: self.app.filters[k] = False
        self.app.id_min_var.set(""); self.app.id_max_var.set("")
        if self.filter_popup:
            for k, w in self.chk_widgets.items(): self._update_chk_vis(k, w)
        self.populate_tree()

    def check_close_filter(self, event):
        if self.filter_popup:
            if event.widget == self.app.btn_filter: return
            try:
                x, y = event.x_root, event.y_root
                fx, fy = self.filter_popup.winfo_rootx(), self.filter_popup.winfo_rooty()
                fw, fh = self.filter_popup.winfo_width(), self.filter_popup.winfo_height()
                if not (fx <= x <= fx+fw and fy <= y <= fy+fh):
                    self.filter_popup.destroy(); self.filter_popup = None
            except: pass

    def show_glossary_window(self):
        # Mantendo sua função corrigida da resposta anterior
        if not self.app.audit_manager.glossary:
            messagebox.showinfo("Glossário", "Nenhum glossário carregado."); return
        c = self.app.current_theme
        win = Toplevel(self.app.root)
        win.title("Visualizador de Glossário"); win.geometry("500x600"); win.configure(bg=c["bg_root"])
        tree = ttk.Treeview(win, columns=("source", "target"), show="headings")
        tree.heading("source", text="Termo Original"); tree.heading("target", text="Tradução Recomendada")
        tree.column("source", width=200); tree.column("target", width=200)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        sb = tk.Scrollbar(win, orient="vertical", command=tree.yview)
        sb.place(relx=1, rely=0, relheight=1, anchor="ne")
        tree.configure(yscroll=sb.set)
        for src, tgt in self.app.audit_manager.glossary.items():
            tree.insert("", "end", values=(src, tgt))