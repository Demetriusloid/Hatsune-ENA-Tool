import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time

class FindReplaceDialog:
    def __init__(self, parent, controller, theme):
        self.controller = controller
        self.c = theme
        self.win = tk.Toplevel(parent)
        self.win.title("Localizar / Substituir")
        self.win.geometry("550x260")
        self.win.configure(bg=self.c["bg_ribbon"])
        self.win.resizable(False, False)
        self.win.transient(parent)
        
        self.v_find = tk.StringVar()
        self.v_replace = tk.StringVar()
        self.v_case = tk.BooleanVar(value=False)
        self.v_whole = tk.BooleanVar(value=False)
        self.win.bind('<Return>', lambda e: self.controller.find_next_action(self.v_find, self.v_case, self.v_whole))
        self._setup_ui()

    def _setup_ui(self):
        b_style = {"bg": self.c["border"], "fg": self.c["fg_text"], "relief": "raised", "bd": 1, "padx": 8, "pady": 4}
        b_action_style = {"bg": self.c["accent"], "fg": "white", "relief": "flat", "bd": 0, "padx": 10, "pady": 4}
        style = ttk.Style()
        style.configure("TNotebook", background=self.c["bg_ribbon"])
        style.configure("TNotebook.Tab", background=self.c["border"], foreground=self.c["fg_text"], padding=[15, 3])
        style.map("TNotebook.Tab", background=[("selected", self.c["bg_root"])])
        
        notebook = ttk.Notebook(self.win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        def create_opts(parent_f):
            opts = tk.Frame(parent_f, bg=self.c["bg_ribbon"])
            opts.pack(fill=tk.X, pady=10)
            tk.Checkbutton(opts, text="Palavra inteira", variable=self.v_whole, bg=self.c["bg_ribbon"], fg=self.c["fg_text"], selectcolor=self.c["bg_ribbon"]).pack(side=tk.LEFT, padx=5)
            tk.Checkbutton(opts, text="Maiúsc/Minúsc", variable=self.v_case, bg=self.c["bg_ribbon"], fg=self.c["fg_text"], selectcolor=self.c["bg_ribbon"]).pack(side=tk.LEFT, padx=5)

        f_find = tk.Frame(notebook, bg=self.c["bg_ribbon"], pady=15, padx=10)
        notebook.add(f_find, text="  Localizar  ")
        tk.Label(f_find, text="Localizar:", bg=self.c["bg_ribbon"], fg=self.c["fg_text"]).pack(anchor="w")
        tk.Entry(f_find, textvariable=self.v_find, bg=self.c["bg_editor"], fg=self.c["fg_text"], insertbackground=self.c["cursor"]).pack(fill=tk.X, pady=(5, 5))
        create_opts(f_find)
        btn_box_f = tk.Frame(f_find, bg=self.c["bg_ribbon"])
        btn_box_f.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        tk.Button(btn_box_f, text="Localizar Próximo", command=lambda: self.controller.find_next_action(self.v_find, self.v_case, self.v_whole), **b_action_style).pack(side=tk.RIGHT, padx=5)

        f_repl = tk.Frame(notebook, bg=self.c["bg_ribbon"], pady=15, padx=10)
        notebook.add(f_repl, text="  Substituir  ")
        tk.Label(f_repl, text="Localizar:", bg=self.c["bg_ribbon"], fg=self.c["fg_text"]).pack(anchor="w")
        tk.Entry(f_repl, textvariable=self.v_find, bg=self.c["bg_editor"], fg=self.c["fg_text"], insertbackground=self.c["cursor"]).pack(fill=tk.X, pady=2)
        tk.Label(f_repl, text="Substituir por:", bg=self.c["bg_ribbon"], fg=self.c["fg_text"]).pack(anchor="w")
        tk.Entry(f_repl, textvariable=self.v_replace, bg=self.c["bg_editor"], fg=self.c["fg_text"], insertbackground=self.c["cursor"]).pack(fill=tk.X, pady=2)
        create_opts(f_repl)
        btn_box_r = tk.Frame(f_repl, bg=self.c["bg_ribbon"])
        btn_box_r.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        tk.Button(btn_box_r, text="Substituir", command=lambda: self.controller.replace_current(self.v_find, self.v_replace, self.v_case, self.v_whole), **b_action_style).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_box_r, text="Substituir Tudo", command=lambda: self.controller.replace_all(self.v_find, self.v_replace, self.v_case, self.v_whole), **b_style).pack(side=tk.LEFT, padx=0)

class ProgressPopup:
    def __init__(self, parent, theme, start, end, cancel_callback):
        self.c = theme
        self.win = tk.Toplevel(parent)
        self.win.title("Escaneando...")
        self.win.geometry("400x180")
        self.win.configure(bg=self.c["bg_ribbon"])
        self.win.transient(parent)
        x = parent.winfo_x() + (parent.winfo_width()//2) - 200
        y = parent.winfo_y() + (parent.winfo_height()//2) - 90
        self.win.geometry(f"+{x}+{y}")
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(self.win, variable=self.progress_var, maximum=(end-start+1)).pack(fill=tk.X, padx=20, pady=20)
        self.lbl_info = tk.Label(self.win, text="Iniciando...", bg=self.c["bg_ribbon"], fg=self.c["fg_text"])
        self.lbl_info.pack()
        tk.Button(self.win, text="Cancelar", command=cancel_callback, bg=self.c["error_spell"], fg="white").pack(pady=10)
        self.win.protocol("WM_DELETE_WINDOW", cancel_callback)

    def update(self, idx, count, total, elapsed, avg):
        if not self.win.winfo_exists(): return
        self.progress_var.set(count)
        self.lbl_info.config(text=f"Processando ID: {idx} ({count}/{total})")
    
    def destroy(self):
        if self.win.winfo_exists(): self.win.destroy()