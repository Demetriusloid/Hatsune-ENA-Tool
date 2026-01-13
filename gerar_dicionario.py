import json
import gzip
import os
import urllib.request
import ssl

# URL da lista de palavras (Github)
URL_WORDLIST = "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt"

# Configura caminhos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
OUTPUT_FILE = os.path.join(SRC_DIR, "pt_BR.json.gz")

# --- LISTA DE SEGURANÇA (Palavras comuns com Alta Frequência) ---
# Isso ensina o corretor que estas palavras são MUITO mais prováveis que as obscuras.
PALAVRAS_COMUNS = [
    "a", "o", "as", "os", "um", "uma", "uns", "umas",
    "eu", "tu", "ele", "ela", "nós", "vós", "eles", "elas", "você", "vocês",
    "me", "te", "se", "lhe", "nos", "vos", "lhes", "mim", "ti", "si",
    "meu", "teu", "seu", "nosso", "vosso", "minha", "tua", "sua", "nossa", "vossa",
    "este", "esse", "aquele", "esta", "essa", "aquela", "isto", "isso", "aquilo",
    "que", "quem", "qual", "quais", "quanto", "quantos", "onde", "como", "quando",
    "não", "sim", "talvez", "jamais", "nunca", "sempre", "agora", "hoje", "ontem",
    "aqui", "ali", "lá", "cá", "longe", "perto",
    "e", "nem", "mas", "porém", "todavia", "contudo", "entretanto", "ou", "pois", "porque", "porquê",
    "que", "se", "como", "embora", "conforme", "segundo", "para", "por", "de", "em", "com",
    "ser", "estar", "ter", "haver", "ir", "vir", "fazer", "dizer", "poder", "ver",
    "sou", "és", "é", "somos", "sois", "são", "era", "fui", "serei", "seria",
    "estou", "estás", "está", "estamos", "estais", "estão", "estava", "estive",
    "tenho", "tens", "tem", "temos", "tendes", "têm", "tinha", "tive",
    "há", "houve", "haverá",
    "foi", "vai", "vão", "vem", "vêm", "fez", "faz", "diz", "pode", "vê",
    "coisa", "casa", "tempo", "ano", "dia", "vez", "homem", "mulher", "senhor", "senhora",
    "tão", "muito", "pouco", "mais", "menos", "bastante", "demais",
    "bom", "mau", "bem", "mal", "grande", "pequeno", "novo", "velho", "primeiro", "último",
    "ena", "moony", "turrón", "turron", "sales", "mean", "jumpscare" # Whitelist do Jogo
]

def gerar():
    print(f"--- GERADOR DE DICIONÁRIO PT-BR OTIMIZADO ---")
    
    if not os.path.exists(SRC_DIR): os.makedirs(SRC_DIR)

    # 1. Download
    print("Baixando lista completa...")
    ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(URL_WORDLIST, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=20) as response:
            conteudo = response.read().decode('utf-8', errors='ignore')
            palavras_raw = conteudo.splitlines()
    except Exception as e:
        print(f"❌ Erro no download: {e}")
        return

    print(f"Processando {len(palavras_raw)} palavras...")

    # 2. Construção do Dicionário
    # Frequência 1 para palavras normais
    dicionario_json = {p.strip().lower(): 1 for p in palavras_raw if p.strip()}

    # 3. Aplicação da Alta Frequência (Override)
    # Frequência 5000 para palavras comuns (garante que sejam a sugestão principal)
    count_comuns = 0
    for w in PALAVRAS_COMUNS:
        w_clean = w.strip().lower()
        dicionario_json[w_clean] = 5000
        count_comuns += 1

    # 4. Salvar
    print(f"Salvando dicionário otimizado em: {OUTPUT_FILE}")
    try:
        with gzip.open(OUTPUT_FILE, 'wt', encoding='utf-8') as f:
            json.dump(dicionario_json, f, ensure_ascii=False)
        print("\n✨ SUCESSO! O arquivo foi gerado com prioridade para PT-BR.")
        print(f"Total de termos: {len(dicionario_json)}")
        print(f"Termos de alta prioridade injetados: {count_comuns}")
        print("Agora execute 'python main.py' e teste a correção.")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

if __name__ == "__main__":
    gerar()