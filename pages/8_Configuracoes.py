import streamlit as st
import json
import os
import pandas as pd
import time
from modules.ui import configurar_pagina_padrao

# 1. Aplica o visual vermelho
configurar_pagina_padrao()

st.title("⚙️ Configurações do Sistema")

# --- SEGURANÇA (Apenas Admin) ---
if st.session_state.get('perfil') != 'admin':
    st.error("⛔ Acesso Negado: Área restrita para Administradores.")
    st.stop()

# --- CAMINHOS DOS ARQUIVOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_USUARIOS = os.path.join(BASE_DIR, 'dados', 'usuarios.json')
FILE_CLIENTES = os.path.join(BASE_DIR, 'dados', 'clientes.json')
FILE_PRODUTOS = os.path.join(BASE_DIR, 'dados', 'produtos.json')

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_usuarios():
    if not os.path.exists(FILE_USUARIOS): return []
    try:
        with open(FILE_USUARIOS, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def salvar_usuarios(lista):
    with open(FILE_USUARIOS, 'w', encoding='utf-8') as f: 
        json.dump(lista, f, indent=4, ensure_ascii=False)

# --- INICIALIZAÇÃO DE ESTADO ---
if 'editando_user' not in st.session_state:
    st.session_state.editando_user = None

# --- LISTA DE PERFIS DISPONÍVEIS ---
LISTA_PERFIS = ["vendedor", "tecnico", "medico", "admin"]

# --- INTERFACE ---
tab_equipe, tab_backup = st.tabs(["👥 Gestão de Equipe", "💾 Backup & Dados"])

# ==================================================
# ABA 1: GESTÃO DE EQUIPE
# ==================================================
with tab_equipe:
    users = carregar_usuarios()
    
    col_esquerda, col_direita = st.columns([1.5, 1])
    
    # --- LADO ESQUERDO: LISTA ---
    with col_esquerda:
        st.subheader("Usuários Ativos")
        
        if users:
            for i, u in enumerate(users):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.markdown(f"**{u['nome']}**")
                        st.caption(f"Login: `{u['usuario']}` | Perfil: {u['perfil'].upper()}")
                    
                    with c2:
                        # Botão EDITAR
                        if st.button("✏️", key=f"btn_edit_{i}", help="Editar Usuário"):
                            st.session_state.editando_user = i
                            st.rerun()
                    
                    with c3:
                        # Botão EXCLUIR
                        if str(u['usuario']).lower() == 'admin':
                            st.button("⛔", disabled=True, key=f"btn_del_{i}")
                        else:
                            if st.button("🗑️", key=f"btn_del_{i}", help="Excluir Usuário"):
                                users.pop(i)
                                salvar_usuarios(users)
                                st.success("Removido!")
                                time.sleep(0.5)
                                st.rerun()
        else:
            st.info("Nenhum usuário cadastrado.")

    # --- LADO DIREITO: FORMULÁRIO ---
    with col_direita:
        # MODO EDIÇÃO
        if st.session_state.editando_user is not None:
            idx = st.session_state.editando_user
            if idx < len(users):
                usuario_atual = users[idx]
                st.subheader(f"✏️ Editando: {usuario_atual['nome']}")
                
                with st.form("form_editar"):
                    e_nome = st.text_input("Nome", value=usuario_atual['nome'])
                    e_login = st.text_input("Login", value=usuario_atual['usuario'], disabled=True)
                    e_senha = st.text_input("Nova Senha", value=usuario_atual['senha'], type="password")
                    
                    idx_perfil = 0
                    if usuario_atual['perfil'] in LISTA_PERFIS:
                        idx_perfil = LISTA_PERFIS.index(usuario_atual['perfil'])
                        
                    e_perfil = st.selectbox("Perfil", LISTA_PERFIS, index=idx_perfil)
                    
                    c_salvar, c_cancelar = st.columns(2)
                    if c_salvar.form_submit_button("💾 Salvar Alterações"):
                        users[idx]['nome'] = e_nome
                        users[idx]['senha'] = e_senha
                        users[idx]['perfil'] = e_perfil
                        salvar_usuarios(users)
                        st.session_state.editando_user = None
                        st.success("Atualizado!")
                        st.rerun()
                    
                    if c_cancelar.form_submit_button("❌ Cancelar"):
                        st.session_state.editando_user = None
                        st.rerun()
            else:
                st.session_state.editando_user = None
                st.rerun()

        # MODO NOVO CADASTRO
        else:
            st.subheader("➕ Novo Cadastro")
            with st.form("form_novo"):
                n_nome = st.text_input("Nome Completo")
                n_login = st.text_input("Login de Acesso")
                n_senha = st.text_input("Senha", type="password")
                n_perfil = st.selectbox("Perfil", LISTA_PERFIS)
                
                if st.form_submit_button("Cadastrar Usuário"):
                    if any(u['usuario'] == n_login for u in users):
                        st.error("Login já existe!")
                    elif n_nome and n_login and n_senha:
                        users.append({
                            "usuario": n_login,
                            "senha": n_senha,
                            "nome": n_nome,
                            "perfil": n_perfil
                        })
                        salvar_usuarios(users)
                        st.success("Criado!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Preencha tudo.")

# ==================================================
# ABA 2: BACKUP (CORRIGIDA)
# ==================================================
with tab_backup:
    st.subheader("Segurança da Informação")
    st.markdown("Faça o download periódico dos seus dados.")
    
    c1, c2, c3 = st.columns(3)
    
    # Bloco Clientes
    if os.path.exists(FILE_CLIENTES):
        with open(FILE_CLIENTES, "r", encoding='utf-8') as f:
            c1.download_button("📥 Baixar Clientes", f, "backup_clientes.json", "application/json")
    else:
        c1.warning("Sem clientes.")

    # Bloco Estoque
    if os.path.exists(FILE_PRODUTOS):
        with open(FILE_PRODUTOS, "r", encoding='utf-8') as f:
            c2.download_button("📥 Baixar Estoque", f, "backup_estoque.json", "application/json")
    else:
        c2.warning("Sem estoque.")
            
    # Bloco Usuários
    if os.path.exists(FILE_USUARIOS):
        with open(FILE_USUARIOS, "r", encoding='utf-8') as f:
            c3.download_button("📥 Baixar Usuários", f, "backup_usuarios.json", "application/json")
    else:
        c3.warning("Sem usuários.")