import tkinter as tk
from tkinter import ttk
import webbrowser
from ..logic.backend import MT_AVAILABLE

def setup_ui(app):
    c = app.current_theme
    
    app.ribbon_frame = tk.Frame(app.root, height=80, padx=5, pady=10)
    app.ribbon_frame.pack(side=tk.TOP, fill=tk.X)
    
    # --- HEADER: Botão de Reset e Status (Lado Direito) ---
    btn_reset = tk.Button(app.ribbon_frame, text="🗑️", command=app.file_ctrl.unload_all_files,
                          bg=c["bg_ribbon"], fg="#e74c3c", relief="flat", font=("Segoe UI", 7), bd=0)
    btn_reset.pack(side=tk.RIGHT, anchor="ne", padx=(5, 10), pady=0)
    
    app.lbl_status = tk.Label(app.ribbon_frame, text="", font=("Segoe UI", 9))
    app.lbl_status.pack(side=tk.RIGHT, anchor="n", padx=5, pady=5)

    # ================= GRUPO: ARQUIVO =================
    app.file_group = tk.Frame(app.ribbon_frame, bg=c["bg_ribbon"])
    app.file_group.pack(side=tk.LEFT, padx=(0, 15), anchor="n")
    
    app.file_header = tk.Frame(app.file_group, bg=c["bg_ribbon"])
    app.file_header.pack(anchor="w", fill=tk.X)
    app.lbl_file = tk.Label(app.file_header, text="ARQUIVO", font=("Segoe UI", 8, "bold"))
    app.lbl_file.pack(side=tk.LEFT)
    app.lbl_credits = tk.Label(app.file_header, text="By @demetriusloid", font=("Segoe UI", 8, "italic"), cursor="hand2")
    app.lbl_credits.pack(side=tk.LEFT, padx=(5, 0))
    app.lbl_credits.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/demetriusloid"))
    
    # Botões do grupo Arquivo
    ttk.Button(app.file_group, text="📂 Base", command=app.file_ctrl.load_base_file).pack(side=tk.LEFT, padx=1)
    
    app.btn_import_trans = ttk.Button(app.file_group, text="📂 Importar", command=app.file_ctrl.import_translation_file)
    app.btn_import_trans.pack(side=tk.LEFT, padx=1)
    app.btn_import_trans.config(state=tk.DISABLED)
    
    app.btn_import_partial = ttk.Button(app.file_group, text="📂 Parcial", command=app.file_ctrl.import_partial_file)
    app.btn_import_partial.pack(side=tk.LEFT, padx=1)
    app.btn_import_partial.config(state=tk.DISABLED)
    
    app.btn_export_mod = ttk.Button(app.file_group, text="💾 Seleção", command=app.file_ctrl.open_export_selector)
    app.btn_export_mod.pack(side=tk.LEFT, padx=1)
    app.btn_export_mod.config(state=tk.DISABLED)
    
    ttk.Button(app.file_group, text="💾 Salvar Tudo", command=app.file_ctrl.save_file).pack(side=tk.LEFT, padx=1)

    # ================= GRUPO: GLOSSÁRIO =================
    app.glossary_group = tk.Frame(app.ribbon_frame, bg=c["bg_ribbon"])
    app.glossary_group.pack(side=tk.LEFT, padx=(0, 15), anchor="n")
    
    app.lbl_glossary = tk.Label(app.glossary_group, text="GLOSSÁRIO", font=("Segoe UI", 8, "bold"))
    app.lbl_glossary.pack(anchor="w")
    
    app.btn_load_glossary = ttk.Button(app.glossary_group, text="📚 Carregar", command=app.audit_manager.load_glossary)
    app.btn_load_glossary.pack(side=tk.LEFT, padx=1)
    app.btn_view_glossary = ttk.Button(app.glossary_group, text="👁️ Ver", command=app.tree_ctrl.show_glossary_window)
    app.btn_view_glossary.pack(side=tk.LEFT, padx=1)

    # ================= GRUPO: EDIÇÃO =================
    app.edit_group = tk.Frame(app.ribbon_frame, bg=c["bg_ribbon"])
    app.edit_group.pack(side=tk.LEFT, padx=(0, 15), anchor="n")
    
    app.lbl_edit = tk.Label(app.edit_group, text="EDIÇÃO", font=("Segoe UI", 8, "bold"))
    app.lbl_edit.pack(anchor="w")
    app.lbl_edit.bind("<Button-1>", app.open_secret_video)
    app.lbl_edit.configure(cursor="hand2")
    
    app.btn_replace = ttk.Button(app.edit_group, text="🔍 Localizar", command=app.editor_ctrl.show_advanced_find)
    app.btn_replace.pack(side=tk.LEFT, padx=1)
    app.btn_session_log = ttk.Button(app.edit_group, text="📋 Log Global", command=app.editor_ctrl.show_session_log_window)
    app.btn_session_log.pack(side=tk.LEFT, padx=1)

    # ================= GRUPO: VISUALIZAÇÃO =================
    app.audit_group = tk.Frame(app.ribbon_frame, bg=c["bg_ribbon"])
    app.audit_group.pack(side=tk.LEFT, padx=(0, 5), anchor="n")
    
    app.lbl_audit = tk.Label(app.audit_group, text="VISUALIZAÇÃO", font=("Segoe UI", 8, "bold"))
    app.lbl_audit.pack(anchor="w")
    app.lbl_audit.bind("<Button-1>", app.tree_ctrl.toggle_spy_mode)
    
    mt_state = tk.NORMAL if MT_AVAILABLE else tk.DISABLED
    mt_text = "Tradutor" if MT_AVAILABLE else "Tradutor (N/A)"
    audit_font = ("Segoe UI", 8)

    # Container interno para os checkboxes
    chk_frame = tk.Frame(app.audit_group, bg=c["bg_ribbon"])
    
    # --- CORREÇÃO DE ALINHAMENTO AQUI ---
    # Adicionei pady=(3, 0) para empurrar os checkboxes para baixo e alinhar com os botões
    chk_frame.pack(anchor="w", pady=(3, 0))

    # Configuração comum para Checkbuttons sem borda
    chk_opts = {"font": audit_font, "bd": 0, "highlightthickness": 0, "relief": "flat"}

    app.chk_baseline = tk.Checkbutton(chk_frame, text="Zer. Verdes", variable=app.use_custom_baseline, 
                                       command=app.tree_ctrl.toggle_custom_baseline, **chk_opts)
    app.chk_baseline.pack(side=tk.LEFT, padx=3)
    
    app.chk_mt = tk.Checkbutton(chk_frame, text=mt_text, variable=app.show_mt, 
                                 command=app.editor_ctrl.toggle_mt_view, state=mt_state, **chk_opts)
    app.chk_mt.pack(side=tk.LEFT, padx=3)
    
    app.chk_spell = tk.Checkbutton(chk_frame, text="Ortografia", variable=app.show_spell, command=app.editor_ctrl.refresh_audit_view, **chk_opts)
    app.chk_spell.pack(side=tk.LEFT, padx=3)

    app.chk_tags = tk.Checkbutton(chk_frame, text="Tags", variable=app.show_tags, command=app.editor_ctrl.refresh_audit_view, **chk_opts)
    app.chk_tags.pack(side=tk.LEFT, padx=3)

    app.chk_grammar = tk.Checkbutton(chk_frame, text="Gramática", variable=app.show_grammar, command=app.editor_ctrl.refresh_audit_view, **chk_opts)
    app.chk_grammar.pack(side=tk.LEFT, padx=3)

    app.chk_glossary = tk.Checkbutton(chk_frame, text="Glossário", variable=app.show_glossary, command=app.editor_ctrl.refresh_audit_view, **chk_opts)
    app.chk_glossary.pack(side=tk.LEFT, padx=3)

    # ================= LAYOUT PRINCIPAL =================
    app.main_pane = tk.PanedWindow(app.root, orient=tk.HORIZONTAL, sashwidth=2)
    app.main_pane.pack(fill=tk.BOTH, expand=True)

    # --- LADO ESQUERDO (Lista) ---
    app.left_frame = tk.Frame(app.main_pane)
    app.main_pane.add(app.left_frame, width=420)
    
    app.search_frame = tk.Frame(app.left_frame, pady=5, padx=5)
    app.search_frame.pack(fill=tk.X)
    
    app.btn_filter = tk.Label(app.search_frame, text="🌪️ Filtros", cursor="hand2", padx=10, pady=5, font=("Segoe UI", 9, "bold"))
    app.btn_filter.pack(side=tk.RIGHT, padx=(5, 0))
    app.btn_filter.bind("<Button-1>", app.tree_ctrl.toggle_filter_popup)
    
    app.lbl_search_icon = tk.Label(app.search_frame, text="🔍")
    app.lbl_search_icon.pack(side=tk.LEFT)
    app.entry_search = tk.Entry(app.search_frame, relief="flat")
    app.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    app.entry_search.bind("<KeyRelease>", app.tree_ctrl.filter_list)

    app.tree_container = tk.Frame(app.left_frame)
    app.tree_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    app.tree = ttk.Treeview(app.tree_container, columns=("#1", "#2", "#3"), show='headings')
    app.tree.heading("#1", text="ID"); app.tree.heading("#2", text="Texto"); app.tree.heading("#3", text="Status")
    app.tree.column("#1", width=50, anchor="center", stretch=False)
    app.tree.column("#2", width=280)
    app.tree.column("#3", width=70, anchor="center", stretch=False)
    
    app.scrollbar = tk.Scrollbar(app.tree_container, orient="vertical", command=app.tree.yview)
    app.tree.configure(yscroll=app.scrollbar.set)
    app.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    app.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    app.tree.bind("<Button-1>", app.tree_ctrl.handle_tree_click)
    app.tree.bind("<<TreeviewSelect>>", app.editor_ctrl.on_select)
    app.tree.bind("<Motion>", app.tree_ctrl.on_tree_hover)
    app.tree.bind("<Leave>", app.editor_ctrl.hide_tooltip)
    
    tk.Frame(app.tree_container, width=1, bg="#333333").place(x=50, y=0, relheight=1)

    # --- LADO DIREITO (Editor) ---
    app.right_frame = tk.Frame(app.main_pane, padx=20, pady=20)
    app.main_pane.add(app.right_frame)
    
    app.lbl_orig = tk.Label(app.right_frame, text="Texto Original (Inglês):", font=("Segoe UI", 9))
    app.lbl_orig.pack(anchor="w")
    
    app.txt_original = tk.Text(app.right_frame, height=5, font=("Consolas", 11), relief="flat", padx=10, pady=10, bd=0)
    app.txt_original.pack(fill=tk.X, pady=(0, 10))
    app.txt_original.config(state=tk.DISABLED)

    app.lbl_mt_header = tk.Label(app.right_frame, text="Sugestão Automática:", font=("Segoe UI", 8, "bold"))
    app.txt_mt = tk.Text(app.right_frame, height=4, font=("Consolas", 10), relief="flat", padx=10, pady=5, bd=0, wrap=tk.WORD)

    app.header_frame = tk.Frame(app.right_frame, bg=c["bg_root"])
    app.lbl_trans = tk.Label(app.header_frame, text="Sua Tradução", font=("Segoe UI", 9, "bold"))
    app.lbl_trans.pack(side=tk.LEFT)
    
    app.btn_history = tk.Button(app.header_frame, text="📜 Histórico", command=app.editor_ctrl.open_history_window, 
                                relief="flat", font=("Segoe UI", 8), padx=5, pady=0)
                                
    app.chk_ignore = tk.Checkbutton(app.header_frame, variable=app.var_ignore_error, 
                                    command=app.editor_ctrl.on_toggle_ignore, cursor="hand2")
    app.chk_ignore.pack(side=tk.LEFT, padx=5)
    app.chk_ignore.bind("<Enter>", lambda e: app.editor_ctrl.show_tooltip("Ignorar Alertas (Perdoar Linha)", e.x_root, e.y_root + 20))
    app.chk_ignore.bind("<Leave>", app.editor_ctrl.hide_tooltip)

    app.lbl_tag_alert = tk.Label(app.right_frame, text="", font=("Segoe UI", 10, "bold"), fg="red", justify=tk.LEFT)
    
    app.txt_translation = tk.Text(app.right_frame, height=10, font=("Consolas", 12), relief="flat", padx=10, pady=10, 
                                  undo=True, maxundo=0, autoseparators=True, bd=0)
                                  
    app.txt_translation.bind("<KeyRelease>", app.editor_ctrl.on_edit_text)
    app.txt_translation.bind("<Button-3>", app.editor_ctrl.show_context_menu)
    app.txt_translation.bind("<Motion>", app.editor_ctrl.on_text_motion)
    app.txt_translation.bind("<Leave>", lambda e: app.editor_ctrl.hide_tooltip())
    app.txt_translation.bind("<Tab>", app.editor_ctrl.on_tab_pressed)
    app.txt_translation.bind("<space>", app.editor_ctrl.add_undo_separator)
    app.txt_translation.bind("<Return>", app.editor_ctrl.add_undo_separator)

    apply_theme(app)

def apply_theme(app):
    c = app.current_theme
    app.root.configure(bg=c["bg_root"])
    app.ribbon_frame.configure(bg=c["bg_ribbon"])
    
    # Configure todos os frames de grupo com a cor de fundo correta
    for f in [app.file_group, app.file_header, app.edit_group, app.audit_group, app.glossary_group]:
        f.configure(bg=c["bg_ribbon"])

    labels = [app.lbl_status, app.lbl_file, app.lbl_edit, app.lbl_glossary, app.lbl_audit] 
    for lbl in labels: lbl.configure(bg=c["bg_ribbon"], fg=c["fg_text"])
    
    app.lbl_status.configure(fg=c["fg_dim"])
    app.lbl_credits.configure(bg=c["bg_ribbon"], fg=c["fg_dim"]) 
    app.lbl_file.configure(fg=c["accent"])
    app.lbl_edit.configure(fg=c["accent"]) 
    app.lbl_glossary.configure(fg=c["accent"])
    app.lbl_audit.configure(bg=c["bg_ribbon"], fg=c["mt_match"] if app.spy_mode else c["audit_label"])
    
    switches = [app.chk_spell, app.chk_tags, app.chk_grammar, app.chk_glossary, app.chk_mt, app.chk_baseline]
    for chk in switches:
        if chk: chk.configure(bg=c["bg_ribbon"], fg=c["fg_text"], selectcolor=c["bg_ribbon"], activebackground=c["bg_ribbon"], activeforeground=c["fg_text"])
        
    app.main_pane.configure(bg=c["bg_root"])
    app.left_frame.configure(bg=c["bg_list"])
    app.right_frame.configure(bg=c["bg_root"])
    app.search_frame.configure(bg=c["bg_list"])
    app.tree_container.configure(bg=c["bg_list"])
    app.btn_filter.configure(bg=c["filter_btn_inactive"], fg="white")
    app.lbl_search_icon.configure(bg=c["bg_list"], fg=c["fg_dim"])
    app.lbl_orig.configure(bg=c["bg_root"], fg=c["fg_text"])
    app.lbl_trans.configure(bg=c["bg_root"], fg=c["fg_text"])
    app.lbl_tag_alert.configure(bg=c["bg_root"]) 
    app.lbl_mt_header.configure(bg=c["bg_root"], fg=c["accent"])
    app.txt_mt.configure(bg=c["mt_bg"], fg=c["mt_fg"], highlightthickness=1, highlightbackground=c["border"])
    app.entry_search.configure(bg=c["bg_editor"], fg=c["fg_text"], insertbackground=c["cursor"])
    app.txt_original.configure(bg=c["bg_readonly"], fg=c["fg_dim"], highlightthickness=1, highlightbackground=c["border"])
    app.txt_translation.configure(bg=c["bg_editor"], fg=c["fg_text"], insertbackground=c["cursor"], highlightthickness=1, highlightbackground=c["border"])
    app.scrollbar.configure(bg=c["sb_bg"], troughcolor=c["sb_trough"], activebackground=c["sb_active"], borderwidth=0, elementborderwidth=0)
    
    app.txt_translation.tag_configure("tag_xml", foreground=c["tag_xml"])
    app.txt_translation.tag_configure("tag_ena", foreground=c["tag_ena"])
    app.txt_translation.tag_configure("misspelled", foreground=c["error_spell"], underline=True)
    app.txt_translation.tag_configure("grammar_error", foreground=c["error_punct"], underline=True)
    app.txt_translation.tag_configure("tag_error", background=c["error_tag"], foreground="white")
    app.txt_translation.tag_configure("glossary_case_error", foreground=c["glossary_warn"], underline=True)
    app.txt_translation.tag_configure("search_highlight", background=c["search_highlight"], foreground="white")
    
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TButton", background=c["bg_ribbon"], foreground=c["fg_text"], borderwidth=0, focuscolor=c["bg_ribbon"])
    style.map("TButton", background=[("active", c["border"])], foreground=[("active", c["fg_text"])])
    style.configure("Treeview", background=c["bg_list"], fieldbackground=c["bg_list"], foreground=c["fg_text"], borderwidth=0, rowheight=25)
    style.configure("Treeview.Heading", background=c["bg_ribbon"], foreground=c["fg_text"], relief="flat")
    style.map("Treeview", background=[("selected", c["selection_bg"])], foreground=[("selected", c["fg_text"])]) 
    
    app.tree.tag_configure('modified', foreground=c["modified_item"]) 
    app.tree.tag_configure('alert', foreground=c["alert_icon"]) 
    app.tree.tag_configure('mt_match', foreground=c["mt_match"]) 
    app.tree.tag_configure('glossary_issue', foreground=c["glossary_warn"]) 
    
    app.header_frame.configure(bg=c["bg_root"])
    app.btn_history.configure(bg=c["btn_subtle"], fg=c["fg_text"])
    app.chk_ignore.configure(bg=c["bg_root"], fg=c["fg_text"], selectcolor=c["bg_root"], activebackground=c["bg_root"])