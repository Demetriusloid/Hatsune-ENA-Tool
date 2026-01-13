import re
import json
import os
from collections import Counter
from tkinter import filedialog, messagebox
from ..config import resource_path, remove_accents

try:
    from spellchecker import SpellChecker
    SPELL_AVAILABLE = True
except ImportError:
    SPELL_AVAILABLE = False

class AuditManager:
    def __init__(self):
        self.spell = None
        self.glossary = {}
        self._init_spellchecker()

    def _init_spellchecker(self):
        if SPELL_AVAILABLE:
            try:
                # Localiza o dicionário
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir = os.path.dirname(current_dir)
                dict_path = os.path.join(src_dir, "pt_BR.json.gz")
                
                # Tenta carregar o local primeiro, depois o resource (para exe)
                final_path = None
                if os.path.exists(dict_path):
                    final_path = dict_path
                else:
                    alt_path = resource_path(os.path.join("src", "pt_BR.json.gz"))
                    if os.path.exists(alt_path):
                        final_path = alt_path

                if final_path:
                    self.spell = SpellChecker(language=None, local_dictionary=final_path)
                    print(f"✅ Dicionário PT-BR carregado: {final_path}")
                else:
                    print("⚠️ Dicionário não encontrado. Usando padrão.")
                    self.spell = SpellChecker(language='pt')
                
                # Whitelist técnica
                whitelist = [
                    'ena', 'moony', 'turrón', 'turron', 'phr', 'cg', 'ui', 'style', 
                    'br', 'b', 'i', 'font', 'size', 'color', 'div', 'span', 'class',
                    'sales', 'mean', 'jumpscare', 'pra', 'tá', 'né', 'ok', 'vc', 'pq'
                ]
                self.spell.word_frequency.load_words(whitelist)
                
            except Exception as e:
                print(f"❌ Erro no corretor: {e}")
                self.spell = None

    def load_glossary(self):
        filename = filedialog.askopenfilename(title="Carregar Glossário", filetypes=[("JSON Files", "*.json")])
        if not filename: return False
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    self.glossary = data
                    return len(self.glossary)
                else:
                    messagebox.showerror("Erro", "JSON inválido.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ler: {e}")
        return False

    def validate_glossary(self, original, translation):
        if not self.glossary: return []
        issues = []
        original_lower = original.lower()
        trans_lower = translation.lower()
        trans_norm = remove_accents(translation).lower()
        for src, tgt in self.glossary.items():
            if src.lower() in original_lower:
                if tgt in translation: continue
                if tgt.lower() in trans_lower:
                    issues.append(f"Glossário: '{tgt}' (Maiúsc/Minúsc incorreta)")
                    continue
                tgt_norm = remove_accents(tgt).lower()
                if tgt_norm in trans_norm:
                    issues.append(f"Glossário: '{tgt}' (Acentuação incorreta)")
                    continue
                issues.append(f"Glossário: Falta '{tgt}'")
        return issues

    def validate_tags(self, original, translation):
        if translation.count('<') != translation.count('>'): return "Tags quebradas (< >)", "tag_err"
        c_orig = Counter(re.findall(r'<[^>]+>', original))
        c_trans = Counter(re.findall(r'<[^>]+>', translation))
        if c_orig == c_trans: return "Tags OK", "tag_ok"
        return "Tags diferentes ou faltando", "tag_warn"

    def check_grammar_issues(self, text, original):
        if re.search(r' {2,}', text): return "Gramática: Espaços duplos."
        if re.search(r'[\.,;:\?!](?!\s|$|\d|\.)\w', text): return "Pontuação: Falta espaço."
        if re.search(r'\w\s+[\.,;:\?!]', text): return "Pontuação: Espaço antes."
        if re.search(r'([!?:;])\1+', text) and not re.search(r'([!?:;])\1+', original): return "Pontuação repetida."
        return None

    # --- LÓGICA INTELIGENTE DE SUFIXOS ---
    def _is_valid_suffix(self, word):
        """
        Tenta remover sufixos comuns e verifica se a raiz existe no dicionário.
        Ex: Fortão -> Tira 'ão' -> Testa 'Forte', 'Forta', 'Fort'.
        """
        # Lista de sufixos comuns e o tamanho deles
        suffixes = [
            ('mente', 5), # Advérbios (completamente)
            ('íssimo', 6), ('íssima', 6), # Superlativos
            ('inho', 4), ('inha', 4), ('zinho', 5), ('zinha', 5), # Diminutivos
            ('ão', 2), ('ões', 3) # Aumentativos/Plurais
        ]

        for sufixo, tamanho in suffixes:
            if word.endswith(sufixo):
                raiz = word[:-tamanho] # Remove o sufixo
                if len(raiz) < 2: continue
                
                # Tenta verificar a raiz pura e com vogais temáticas comuns (a, o, e)
                # Ex: Fort(ão) -> raiz "Fort". Testa "Fort" (não), "Forte" (sim!)
                # Ex: Complet(amente) -> raiz "Complet". Testa "Completa" (sim!)
                variations = [raiz, raiz + 'a', raiz + 'o', raiz + 'e']
                
                # Remove acentos da raiz se necessário (ex: fácil -> facil-mente)
                # Mas geralmente em PT o acento cai ou muda, vamos testar o básico primeiro.
                
                for attempt in variations:
                    if attempt in self.spell:
                        return True
        return False

    def check_spelling(self, text):
        if not self.spell: return None
        
        # Limpa tags HTML
        clean_text = re.sub(r'<[^>]+>', ' ', text)
        # Regex que pega palavras compostas com hífen
        raw_words = re.findall(r'\b[\w-]+\b', clean_text)
        
        unknowns = []
        
        for word in raw_words:
            w_lower = word.lower()
            
            # 1. Filtros básicos
            if len(w_lower) < 2: continue 
            if any(c.isdigit() for c in w_lower): continue
            
            # 2. Checagem Direta (Dicionário)
            if w_lower in self.spell: continue 
            
            # 3. Tratamento de Hifens (Verbos ênclise)
            # Ex: ajudá-lo
            if '-' in w_lower:
                parts = w_lower.split('-')
                all_parts_ok = True
                for part in parts:
                    if len(part) < 2: continue
                    # Aceita pronomes oblíquos comuns ou se a parte existe no dic
                    if part not in self.spell and part not in ['lo', 'la', 'los', 'las', 'no', 'na', 'nos', 'nas', 'lho', 'lha', 'me', 'te', 'se', 'lhe']:
                        all_parts_ok = False
                        break
                if all_parts_ok: continue

            # 4. Tratamento de Plural Simples
            if w_lower.endswith('s'):
                singular = w_lower[:-1]
                if singular in self.spell: continue

            # 5. Tratamento de Sufixos (Aumentativo, Diminutivo, Mente)
            if self._is_valid_suffix(w_lower):
                continue

            # Se falhou em tudo, é erro
            unknowns.append(word)
                
        return unknowns