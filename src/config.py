import sys
import os
import unicodedata

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

DARK_THEME = {
    "mode": "dark", "bg_root": "#1e1e1e", "bg_ribbon": "#252526", "bg_list": "#191919",
    "bg_editor": "#2b2b2b", "bg_readonly": "#191919",
    "fg_text": "#ffffff", "fg_dim": "#aaaaaa", "accent": "#0078d7",
    "border": "#333333", "cursor": "white",
    "tag_xml": "#ff79c6", "tag_ena": "#8be9fd", "modified_item": "#2ecc71",
    "error_spell": "#ff5555", "error_punct": "#f1c40f", "error_tag": "#e74c3c", "alert_icon": "#e74c3c",
    "tooltip_bg": "#333333", "tooltip_fg": "#ffffff",
    "tag_ok": "#2ecc71", "tag_warn": "#f39c12", "tag_err": "#e74c3c",
    "glossary_warn": "#e67e22",
    "sb_bg": "#3e3e42", "sb_trough": "#252526", "sb_active": "#505050",
    "mt_bg": "#252526", "mt_fg": "#00d2d3",
    "filter_btn_active": "#0078d7", "filter_btn_inactive": "#3e3e42",
    "mt_match": "#bd93f9", "audit_label": "#0078d7", "selection_bg": "#444444",
    "separator_line": "#333333", "search_highlight": "#264f78",
    "btn_subtle": "#3e3e42"
}