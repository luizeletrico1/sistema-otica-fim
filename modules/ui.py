import streamlit as st
import os

def configurar_pagina_padrao():
    # 1. Configura o Nome na Aba do Navegador
    st.set_page_config(
        page_title="Fábrica de Óculos JR Vitória",
        page_icon="👓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 2. CSS GLOBAL
    st.markdown("""
    <style>
        /* Fundo da página principal (Cinza Claro) */
        .stApp { background-color: #f5f5f5; }

        /* --- BARRA LATERAL VERMELHA --- */
        section[data-testid="stSidebar"] { 
            background-color: #FF0000; 
        }
        
        /* --- CORREÇÃO DOS LINKS AZUIS (O Pulo do Gato 🐈) --- */
        /* Força todos os links e textos de navegação a serem BRANCOS */
        section[data-testid="stSidebar"] a,
        section[data-testid="stSidebar"] span,
        [data-testid="stSidebarNav"] a,
        [data-testid="stSidebarNav"] span {
            color: #FFFFFF !important;
            text-decoration: none; /* Tira o sublinhado se tiver */
        }
        
        /* Garante que até o ícone do link seja branco */
        [data-testid="stSidebarNav"] svg {
            fill: #FFFFFF !important;
            color: #FFFFFF !important;
        }

        /* Inputs (Caixas de texto) continuam pretos para ler o que digita */
        [data-testid="stSidebar"] input { 
            color: #000000 !important; 
        }
        
        /* --- MANTER O BOTÃO SAIR FUNCIONANDO (Branco com letras Vermelhas) --- */
        section[data-testid="stSidebar"] button {
            background-color: #FFFFFF !important; /* Fundo Branco */
            border: none !important;
            width: 100%;
        }
        
        /* Texto VERMELHO dentro do botão (sobrepõe a regra do branco acima) */
        section[data-testid="stSidebar"] button * {
            color: #FF0000 !important; 
            font-weight: bold !important;
        }

        /* Logo e linhas divisórias */
        [data-testid="stSidebar"] img { margin-top: 20px; margin-bottom: 10px; }
        [data-testid="stSidebar"] hr { background-color: #FFFFFF; }
        
    </style>
    """, unsafe_allow_html=True)

    # 3. Conteúdo da Barra Lateral
    with st.sidebar:
        # LOGO
        if os.path.exists("logo.png"):
            st.image("logo.png", width=150)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", width=150)
        else:
            st.image("https://cdn-icons-png.flaticon.com/512/3596/3596088.png", width=100)
        
        st.markdown("### Fábrica de Óculos JR Vitória")
        st.markdown("---")
        
        # LOGOUT
        if 'logado' in st.session_state and st.session_state['logado']:
            st.write(f"👤 **{st.session_state.get('usuario_atual', 'Usuário')}**")
            st.write("") 
            
            if st.button("🚪 SAIR DO SISTEMA"):
                st.session_state['logado'] = False
                st.session_state['usuario_atual'] = None
                st.session_state['perfil'] = None
                st.rerun()