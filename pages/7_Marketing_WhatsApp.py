import streamlit as st
import pandas as pd
import json
import os
import urllib.parse
from datetime import datetime
from modules.dados import carregar_dados
from modules.ui import configurar_pagina_padrao

# 1. Visual Padrão
configurar_pagina_padrao()

st.title("📱 Marketing & WhatsApp Inteligente")

# --- CAMINHOS E ARQUIVOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_TEMPLATES = os.path.join(BASE_DIR, 'dados', 'templates_zap.json')
FILE_CONFIG_LOJA = os.path.join(BASE_DIR, 'dados', 'config_loja.json')

# --- FUNÇÕES DE DADOS ---
def carregar_templates():
    if not os.path.exists(FILE_TEMPLATES):
        # Cria alguns modelos padrão se não existir
        padroes = [
            {"titulo": "Aniversário", "texto": "Parabéns {nome}! 🎂 A Fábrica de Óculos JR deseja muitas felicidades. Venha nos visitar!"},
            {"titulo": "Óculos Pronto", "texto": "Olá {nome}, seus óculos ficaram prontos! 😎 Pode vir buscar na loja."},
            {"titulo": "Cobrança Suave", "texto": "Oi {nome}, tudo bem? Vimos que tem uma pendência aqui na ótica. Vamos resolver?"}
        ]
        salvar_templates(padroes)
        return padroes
    try:
        with open(FILE_TEMPLATES, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def salvar_templates(lista):
    os.makedirs(os.path.dirname(FILE_TEMPLATES), exist_ok=True)
    with open(FILE_TEMPLATES, 'w', encoding='utf-8') as f: json.dump(lista, f, indent=4, ensure_ascii=False)

def carregar_config_loja():
    if not os.path.exists(FILE_CONFIG_LOJA): return {"zap_loja": ""}
    try:
        with open(FILE_CONFIG_LOJA, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"zap_loja": ""}

def salvar_config_loja(dados):
    with open(FILE_CONFIG_LOJA, 'w', encoding='utf-8') as f: json.dump(dados, f, indent=4)

def limpar_telefone(tel):
    """Higieniza o telefone para o link do WhatsApp"""
    if not tel: return None
    nums = "".join([c for c in tel if c.isdigit()])
    if len(nums) in [8, 9]: nums = "27" + nums # Assume DDD 27 se não tiver
    if len(nums) in [10, 11]: nums = "55" + nums # Adiciona DDI Brasil
    return nums

def gerar_link(telefone, mensagem):
    tel_limpo = limpar_telefone(telefone)
    if not tel_limpo: return None
    msg_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/{tel_limpo}?text={msg_encoded}"

# --- INICIALIZAÇÃO ---
templates = carregar_templates()
config_loja = carregar_config_loja()
clientes = carregar_dados()

# --- INTERFACE ---
tab_disparo, tab_modelos, tab_config = st.tabs(["🚀 Disparar Mensagens", "📝 Gerenciar Modelos", "⚙️ Configurar Número"])

# ==================================================
# ABA 1: DISPARO DE MENSAGENS
# ==================================================
with tab_disparo:
    st.subheader("📢 Central de Disparos")
    
    col_esq, col_dir = st.columns([1, 2])
    
    with col_esq:
        st.info("1. Escolha o Modelo")
        opcoes_templates = [t['titulo'] for t in templates]
        sel_template = st.selectbox("Selecione a Mensagem:", options=opcoes_templates)
        
        # Pega o texto do template selecionado
        texto_base = ""
        if sel_template:
            template_obj = next(t for t in templates if t['titulo'] == sel_template)
            texto_base = template_obj['texto']
            
        st.text_area("Prévia da Mensagem (Editável):", value=texto_base, height=150, key="msg_envio_final")
        st.caption("Dica: Onde tiver `{nome}`, o sistema troca pelo nome do cliente.")

    with col_dir:
        st.info("2. Selecione os Clientes")
        filtro_tipo = st.radio("Quem vai receber?", ["Buscar por Nome", "Aniversariantes do Mês", "Todos os Clientes"], horizontal=True)
        
        lista_final = []
        
        if filtro_tipo == "Buscar por Nome":
            busca = st.text_input("Digite o nome:")
            if busca:
                lista_final = [c for c in clientes if busca.lower() in c['nome'].lower()]
                
        elif filtro_tipo == "Aniversariantes do Mês":
            mes_sel = st.selectbox("Mês:", range(1, 13), index=datetime.now().month - 1)
            for c in clientes:
                try:
                    dt = c.get("nascimento")
                    if dt:
                        # Tenta formatos comuns
                        d_obj = None
                        if "/" in dt: d_obj = datetime.strptime(dt, "%d/%m/%Y")
                        elif "-" in dt: d_obj = datetime.strptime(dt, "%Y-%m-%d")
                        
                        if d_obj and d_obj.month == mes_sel:
                            lista_final.append(c)
                except: pass
                
        else: # Todos
            st.warning("⚠️ Cuidado ao enviar para muitos contatos de uma vez (Risco de Spam).")
            lista_final = clientes

        # LISTAGEM E BOTÕES
        st.markdown(f"**Encontrados: {len(lista_final)} clientes**")
        st.markdown("---")
        
        # Paginação simples (top 50)
        for c in lista_final[:50]:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                zap = c['contato'].get('whatsapp', '')
                
                c1.markdown(f"👤 **{c['nome']}**")
                c1.caption(f"Tel: {zap}")
                
                # Processa a mensagem (Troca {nome} pelo nome real)
                msg_personalizada = st.session_state.msg_envio_final.replace("{nome}", c['nome'].split()[0])
                
                link = gerar_link(zap, msg_personalizada)
                
                if link:
                    c2.link_button("📲 Enviar", link, type="secondary")
                else:
                    c2.error("Sem Zap")

# ==================================================
# ABA 2: GERENCIAR MODELOS (CRUD)
# ==================================================
with tab_modelos:
    st.subheader("📝 Criar e Editar Mensagens")
    
    # 1. NOVO MODELO
    with st.expander("➕ Criar Novo Modelo", expanded=False):
        with st.form("form_novo_template"):
            novo_titulo = st.text_input("Título do Modelo (Ex: Promoção Dia das Mães)")
            novo_texto = st.text_area("Texto da Mensagem", placeholder="Olá {nome}, venha conferir...")
            st.caption("Use `{nome}` para puxar o nome do cliente automaticamente.")
            
            if st.form_submit_button("Salvar Modelo"):
                if novo_titulo and novo_texto:
                    templates.append({"titulo": novo_titulo, "texto": novo_texto})
                    salvar_templates(templates)
                    st.success("Modelo criado!")
                    st.rerun()
                else:
                    st.warning("Preencha título e texto.")
    
    st.divider()
    
    # 2. LISTA E EDIÇÃO
    st.markdown("#### Modelos Existentes")
    if not templates:
        st.info("Nenhum modelo cadastrado.")
    else:
        for i, t in enumerate(templates):
            with st.container(border=True):
                col_t1, col_t2 = st.columns([4, 1])
                col_t1.markdown(f"**{t['titulo']}**")
                col_t1.text(f"{t['texto'][:60]}...") # Mostra só o começo
                
                if col_t2.button("🗑️ Excluir", key=f"del_temp_{i}"):
                    templates.pop(i)
                    salvar_templates(templates)
                    st.rerun()
                
                with st.expander(f"✏️ Editar: {t['titulo']}"):
                    with st.form(f"edit_form_{i}"):
                        e_titulo = st.text_input("Título", value=t['titulo'])
                        e_texto = st.text_area("Texto", value=t['texto'])
                        if st.form_submit_button("Salvar Alterações"):
                            templates[i] = {"titulo": e_titulo, "texto": e_texto}
                            salvar_templates(templates)
                            st.success("Atualizado!")
                            st.rerun()

# ==================================================
# ABA 3: CONFIGURAÇÃO DA LOJA
# ==================================================
with tab_config:
    st.subheader("⚙️ Configurações do WhatsApp")
    st.info("Aqui você cadastra o número da loja. Futuramente, ele poderá ser usado para assinatura automática nas mensagens.")
    
    with st.form("config_zap"):
        zap_input = st.text_input("WhatsApp da Loja (Com DDD)", value=config_loja.get("zap_loja", ""))
        msg_assinatura = st.text_input("Assinatura Padrão (Opcional)", value=config_loja.get("assinatura", "Att, Equipe Fábrica de Óculos JR"))
        
        if st.form_submit_button("💾 Salvar Configurações"):
            dados_novos = {"zap_loja": zap_input, "assinatura": msg_assinatura}
            salvar_config_loja(dados_novos)
            st.success("Configurações salvas!")