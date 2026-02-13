import streamlit as st
import json
import time
import os
from modules.ui import configurar_pagina_padrao 

# 1. Aplica o visual padrão
configurar_pagina_padrao()

# --- CAMINHO ABSOLUTO DO BANCO DE DADOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_USUARIOS = os.path.join(BASE_DIR, 'dados', 'usuarios.json')

# --- FUNÇÕES ---
def criar_admin_padrao():
    """Cria o admin APENAS se o arquivo não existir"""
    admin_data = [{
        "usuario": "admin",
        "senha": "123",
        "nome": "Administrador",
        "perfil": "admin"
    }]
    os.makedirs(os.path.dirname(ARQUIVO_USUARIOS), exist_ok=True)
    with open(ARQUIVO_USUARIOS, 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, indent=4)
    return admin_data

def carregar_usuarios():
    # Se o arquivo não existe, cria silenciosamente o admin padrão
    if not os.path.exists(ARQUIVO_USUARIOS):
        return criar_admin_padrao()
    
    try:
        with open(ARQUIVO_USUARIOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return criar_admin_padrao()

def login(usuario, senha):
    usuarios_db = carregar_usuarios()
    usuario_lower = str(usuario).lower().strip()
    
    for u in usuarios_db:
        db_user_lower = str(u['usuario']).lower().strip()
        if db_user_lower == usuario_lower and str(u['senha']) == str(senha):
            return u
    return None

# --- GESTÃO DE SESSÃO ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False
    st.session_state['usuario_atual'] = None
    st.session_state['perfil'] = None

# ==================================================
# TELA DE LOGIN (SEM BOTÃO DE RESET)
# ==================================================
if not st.session_state['logado']:
    st.markdown("<h1 style='text-align: center;'>👓 Fábrica de Óculos JR Vitória</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: gray;'>Acesso Restrito ao Sistema</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login_form"):
            user_input = st.text_input("Usuário")
            pass_input = st.text_input("Senha", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            btn_login = st.form_submit_button("🔐 Entrar no Sistema", use_container_width=True)
            
            if btn_login:
                usuario_encontrado = login(user_input, pass_input)
                
                if usuario_encontrado:
                    st.session_state['logado'] = True
                    st.session_state['usuario_atual'] = usuario_encontrado['nome']
                    st.session_state['perfil'] = usuario_encontrado['perfil']
                    st.success(f"Bem-vindo, {usuario_encontrado['nome']}!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

# ==================================================
# TELA DE BOAS-VINDAS (LOGADO)
# ==================================================
else:
    st.title("🏠 Bem-vindo à Fábrica de Óculos JR")
    st.markdown("### Selecione um módulo no menu vermelho ao lado 👈")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.info(f"👤 Usuário Conectado: **{st.session_state['usuario_atual']}**")
    with col_b:
        perfil = st.session_state['perfil'].upper()
        if perfil == 'ADMIN':
            st.warning(f"⚙️ Nível de Acesso: **{perfil}**")
        else:
            st.success(f"💼 Nível de Acesso: **{perfil}**")
            
    st.markdown("---")
    st.markdown("""
    ### Atalhos Rápidos:
    * **Vendas:** Vá para 'PDV Vendas' para realizar vendas com baixa automática.
    * **Orçamentos:** Use 'Orçamentos' para simulações sem alterar o estoque.
    * **Clientes:** Use 'Clientes 360' para cadastrar ou consultar histórico.
    """)