import os
import tkinter as tk
from .config import DARK_THEME, resource_path
from .logic.backend import TranslationManager, FileManager
from .logic.audit import AuditManager
from .logic.media import EasterEgg
from .gui.layout import setup_ui
from .controllers.file_controller import FileController
from .controllers.tree_controller import TreeController
from .controllers.editor_controller import EditorController

class ENATranslationTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Hatsune ENA Tool")
        self.root.geometry("1300x800")
        self.root.configure(bg="#1e1e1e")
        self.SESSION_FILE = "ena_session_state.json"

        try:
            icon = resource_path("app.ico")
            if os.path.exists(icon): self.root.iconbitmap(icon)
        except: pass

        # Data & State
        self.translations = {}
        self.base_filepath = ""; self.base_lines = []
        self.current_index = None; self.last_selected_id = None
        self.session_log = []; self.baseline_snapshot = {}
        self.unsaved_changes = False; self.spy_mode = False
        
        # UI Variables
        self.show_spell = tk.BooleanVar(value=False)
        self.show_tags = tk.BooleanVar(value=True)
        self.show_grammar = tk.BooleanVar(value=True)
        self.show_mt = tk.BooleanVar(value=False)
        self.show_glossary = tk.BooleanVar(value=True)
        self.use_custom_baseline = tk.BooleanVar(value=False)
        self.var_ignore_error = tk.BooleanVar(value=False)
        self.id_min_var = tk.StringVar(); self.id_max_var = tk.StringVar()
        self.spy_scan_min = tk.StringVar(); self.spy_scan_max = tk.StringVar()
        self.filters = {"modified": False, "original": False, "alerts": False, "tags": False, "glossary": False, "mt_match": False}

        # Managers & Controllers
        self.current_theme = DARK_THEME
        self.translator_service = TranslationManager()
        self.audit_manager = AuditManager()
        
        self.file_ctrl = FileController(self)
        self.tree_ctrl = TreeController(self)
        self.editor_ctrl = EditorController(self)

        # --- BINDINGS GLOBAIS (Faltavam aqui) ---
        # Conecta atalhos de teclado e mouse aos controladores corretos
        self.root.bind('<Control-s>', self.file_ctrl.save_file)
        self.root.bind('<Control-f>', self.editor_ctrl.focus_search)
        self.root.bind('<Control-h>', self.editor_ctrl.show_advanced_find)
        self.root.bind('<Control-m>', self.tree_ctrl.toggle_spy_mode)
        # Importante para fechar o popup de filtros ao clicar fora
        self.root.bind('<Button-1>', self.tree_ctrl.check_close_filter)

        # Setup UI
        setup_ui(self)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_auto_session()

    def open_secret_video(self, e=None): EasterEgg.play(self.root)
    def mark_unsaved(self): self.unsaved_changes = True; self.root.title("Hatsune ENA Tool *")
    def mark_saved(self): self.unsaved_changes = False; self.root.title("Hatsune ENA Tool")

    def save_auto_session(self):
        if not self.translations: return
        data = {
            "base": self.base_filepath, "idx": self.current_index, "trans": self.translations,
            "log": self.session_log, "base_snap": self.baseline_snapshot, "ui": {
                "spell": self.show_spell.get(), "tags": self.show_tags.get(), "mt": self.show_mt.get()
            },
            "spy_mode": self.spy_mode,
            "filters": self.filters,
            "use_custom_baseline": self.use_custom_baseline.get()
        }
        FileManager.save_session(self.SESSION_FILE, data)

    def load_auto_session(self):
        data = FileManager.load_session(self.SESSION_FILE)
        if not data: return
        self.base_filepath = data.get("base", "")
        if self.base_filepath and os.path.exists(self.base_filepath):
            with open(self.base_filepath, 'r', encoding='utf-8') as f: self.base_lines = f.readlines()
            self.lbl_orig.config(text=f"Original: {os.path.basename(self.base_filepath)}")
        
        raw_t = data.get("trans", {})
        self.translations = {int(k): v for k, v in raw_t.items()}
        self.current_index = data.get("idx")
        self.session_log = data.get("log", [])
        
        # Restore State
        self.filters = data.get("filters", self.filters)
        self.spy_mode = data.get("spy_mode", False)
        self.use_custom_baseline.set(data.get("use_custom_baseline", False))
        snap = data.get("base_snap", {})
        self.baseline_snapshot = {int(k): v for k, v in snap.items()}

        # Restore UI
        ui = data.get("ui", {})
        self.show_spell.set(ui.get("spell", False))
        self.show_tags.set(ui.get("tags", True))
        self.show_mt.set(ui.get("mt", False))
        
        self.tree_ctrl.populate_tree()
        self.editor_ctrl.toggle_mt_view()
        
        if self.spy_mode:
            self.lbl_audit.configure(fg=self.current_theme["mt_match"])

        if self.translations: 
            for b in [self.btn_import_trans, self.btn_import_partial, self.btn_export_mod]: b.config(state="normal")
            if self.current_index is not None and self.current_index in self.translations:
                self.tree.selection_set(self.current_index)
                self.tree.see(self.current_index)
                self.editor_ctrl.on_select(None)

    def on_close(self):
        self.save_auto_session()
        self.root.destroy()