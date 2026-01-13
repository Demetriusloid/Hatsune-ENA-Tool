import os
import re
import json

try:
    from deep_translator import GoogleTranslator
    MT_AVAILABLE = True
except ImportError:
    MT_AVAILABLE = False

class TranslationManager:
    def __init__(self):
        self.translator = None
        if MT_AVAILABLE:
            try:
                self.translator = GoogleTranslator(source='auto', target='pt')
            except Exception as e:
                print(f"Erro ao iniciar tradutor: {e}")

    def translate(self, text):
        if not self.translator: return "Erro: Biblioteca não disponível"
        return self.translator.translate(text)

class FileManager:
    @staticmethod
    def parse_file_to_dict(lines):
        data = {}
        in_values = False
        current_id = 0
        pattern = re.compile(r'^\s*1 string data = (.*)$')
        
        for line_num, line in enumerate(lines):
            if "vector values" in line: in_values = True
            if in_values:
                match = pattern.match(line)
                if match:
                    raw_text = match.group(1).strip()
                    has_quotes = False
                    clean_text = raw_text
                    if len(raw_text) >= 2 and raw_text.startswith('"') and raw_text.endswith('"'):
                        clean_text = raw_text[1:-1]
                        has_quotes = True
                    data[current_id] = {
                        "text": clean_text, "quotes": has_quotes, "original_line": line_num 
                    }
                    current_id += 1
        return data

    @staticmethod
    def save_session(filepath, data):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception: pass

    @staticmethod
    def load_session(filepath):
        if not os.path.exists(filepath): return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception: return None