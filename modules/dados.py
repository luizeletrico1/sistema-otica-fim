import json
import os

# Caminho absoluto para garantir que funciona em qualquer pasta
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Arquivos de Banco de Dados
ARQUIVO_CLIENTES = os.path.join(BASE_DIR, 'dados', 'clientes.json')
ARQUIVO_PRODUTOS = os.path.join(BASE_DIR, 'dados', 'produtos.json') # Novo!

# --- FUNÇÕES DE CLIENTES ---
def carregar_dados():
    """Lê o JSON de Clientes"""
    if not os.path.exists(ARQUIVO_CLIENTES):
        return []
    try:
        with open(ARQUIVO_CLIENTES, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def salvar_dados(lista_clientes):
    """Salva a lista de Clientes"""
    with open(ARQUIVO_CLIENTES, 'w', encoding='utf-8') as f:
        json.dump(lista_clientes, f, indent=4, ensure_ascii=False)

# --- FUNÇÕES DE ESTOQUE (NOVAS) ---
def carregar_produtos():
    """Lê o JSON de Produtos (Estoque)"""
    if not os.path.exists(ARQUIVO_PRODUTOS):
        return []
    try:
        with open(ARQUIVO_PRODUTOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def salvar_produtos(lista_produtos):
    """Salva a lista de Produtos"""
    with open(ARQUIVO_PRODUTOS, 'w', encoding='utf-8') as f:
        json.dump(lista_produtos, f, indent=4, ensure_ascii=False)