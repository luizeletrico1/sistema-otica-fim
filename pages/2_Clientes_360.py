import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, date
from geopy.geocoders import ArcGIS
from modules.dados import carregar_dados, salvar_dados
from modules.ui import configurar_pagina_padrao

# 1. Aplica o visual vermelho e fundo cinza
configurar_pagina_padrao()

st.title("👤 Gestão de Clientes 360º")

# --- CONFIGURAÇÕES DE DIRETÓRIO ---
PASTA_FOTOS = os.path.join("dados", "fotos")
if not os.path.exists(PASTA_FOTOS):
    os.makedirs(PASTA_FOTOS)

# --- FUNÇÕES UTILITÁRIAS ---

def busca_cep_api(cep_input):
    """Consulta a API ViaCEP e retorna os dados do endereço."""
    cep_limpo = str(cep_input).replace("-", "").replace(".", "").strip()
    if len(cep_limpo) == 8:
        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
            data = response.json()
            if "erro" not in data:
                return {
                    "logradouro": data.get("logradouro", ""),
                    "bairro": data.get("bairro", ""),
                    "localidade": data.get("localidade", ""),
                    "uf": data.get("uf", ""),
                    "pais": "Brasil" # ViaCEP é só Brasil
                }
        except:
            pass
    return None

def obter_coordenadas(endereco_completo):
    """Converte endereço em Latitude/Longitude para o mapa."""
    geolocator = ArcGIS()
    try:
        # Tenta geocodificar o endereço
        location = geolocator.geocode(endereco_completo, timeout=5)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

def salvar_foto_perfil(arquivo_foto, id_cliente):
    if arquivo_foto is None: return None
    extensao = arquivo_foto.name.split(".")[-1]
    nome_arquivo = f"cliente_{id_cliente}.{extensao}"
    caminho_completo = os.path.join(PASTA_FOTOS, nome_arquivo)
    with open(caminho_completo, "wb") as f: f.write(arquivo_foto.getbuffer())
    return nome_arquivo

def formatar_data_br(data_str):
    """Tenta mostrar a data no formato DD/MM/AAAA"""
    if not data_str: return "-"
    try:
        if "-" in data_str: # Formato ISO YYYY-MM-DD
            data_obj = datetime.strptime(data_str, "%Y-%m-%d")
            return data_obj.strftime("%d/%m/%Y")
        return data_str
    except:
        return data_str

# --- CARREGAMENTO DE DADOS ---
clientes = carregar_dados()

# --- INTERFACE ---
tab_consulta, tab_novo = st.tabs(["🔍 Consultar & Mapa", "➕ Novo Cadastro Completo"])

# ==================================================
# ABA 1: CONSULTA E MAPA
# ==================================================
with tab_consulta:
    if not clientes:
        st.info("Nenhum cliente cadastrado. Vá na aba 'Novo Cadastro' para começar.")
    else:
        # Seleção de Cliente
        opcoes_busca = [f"{c['id']} - {c['nome']}" for c in clientes]
        selecionado_str = st.selectbox("Selecione o Cliente:", options=opcoes_busca)
        
        if selecionado_str:
            id_selecionado = int(selecionado_str.split(" - ")[0])
            cliente = next(c for c in clientes if c["id"] == id_selecionado)
            index_cliente = clientes.index(cliente)
            
            st.markdown("---")
            
            col_foto, col_dados = st.columns([1, 2])
            
            # --- COLUNA DA ESQUERDA: FOTO E MAPA ---
            with col_foto:
                # Foto
                foto_atual = cliente.get("foto")
                if foto_atual and os.path.exists(os.path.join(PASTA_FOTOS, foto_atual)):
                    st.image(os.path.join(PASTA_FOTOS, foto_atual), width=200)
                else:
                    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
                
                # Upload Foto
                with st.expander("📸 Alterar Foto"):
                    nova_foto = st.file_uploader("Enviar nova foto", type=["jpg", "png"])
                    if st.button("Salvar Foto"):
                        if nova_foto:
                            nome_salvo = salvar_foto_perfil(nova_foto, cliente['id'])
                            clientes[index_cliente]["foto"] = nome_salvo
                            salvar_dados(clientes)
                            st.rerun()

                # Mapa Automático
                st.markdown("### 🗺️ Localização")
                end = cliente.get('endereco', {})
                endereco_str = f"{end.get('logradouro','')}, {end.get('numero','')}, {end.get('municipio','')}, {end.get('estado','')}, {end.get('pais','Brasil')}"
                cep_str = end.get('cep', '')
                
                # Botão para gerar mapa
                if st.button("📍 Carregar Mapa no Google"):
                    with st.spinner("Gerando mapa..."):
                        # Tenta pelo endereço completo, se falhar tenta pelo CEP
                        busca_mapa = endereco_str if len(endereco_str) > 15 else f"{cep_str}, Brasil"
                        lat, lon = obter_coordenadas(busca_mapa)
                        
                    if lat and lon:
                        st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=15)
                    else:
                        st.error("Endereço não encontrado no mapa.")

            # --- COLUNA DA DIREITA: DADOS COMPLETOS ---
            with col_dados:
                st.subheader(f"Ficha de: {cliente['nome']}")
                
                c1, c2, c3 = st.columns(3)
                c1.markdown(f"**CPF:** {cliente.get('cpf', '-')}")
                c2.markdown(f"**RG:** {cliente.get('rg', '-')}")
                c3.markdown(f"**Nascimento:** {formatar_data_br(cliente.get('nascimento', ''))}")
                
                st.markdown(f"**Telefone:** {cliente['contato'].get('telefone', '-')}")
                st.markdown(f"**WhatsApp:** {cliente['contato'].get('whatsapp', '-')}")
                
                st.divider()
                st.markdown("#### 🏠 Endereço")
                e = cliente.get('endereco', {})
                st.text(f"CEP: {e.get('cep','-')}")
                st.text(f"{e.get('logradouro','-')}, {e.get('numero','-')}")
                st.text(f"Bairro: {e.get('bairro','-')}")
                st.text(f"{e.get('municipio','-')} - {e.get('estado','-')}")
                st.text(f"País: {e.get('pais','-')}")
                
                # Botão de Exclusão
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Excluir Cliente", type="primary"):
                    clientes.pop(index_cliente)
                    salvar_dados(clientes)
                    st.success("Cliente removido!")
                    st.rerun()

# ==================================================
# ABA 2: NOVO CADASTRO
# ==================================================
with tab_novo:
    st.subheader("📝 Ficha Cadastral")
    
    with st.form("form_novo_cliente"):
        # GRUPO 1: DADOS PESSOAIS
        st.markdown("##### 1. Dados Pessoais")
        col_nome, col_nasc = st.columns([3, 1])
        n_nome = col_nome.text_input("Nome Completo *")
        n_nasc = col_nasc.date_input("Data de Nascimento", min_value=date(1920, 1, 1), format="DD/MM/YYYY")
        
        c_cpf, c_rg = st.columns(2)
        n_cpf = c_cpf.text_input("CPF")
        n_rg = c_rg.text_input("RG")
        
        # GRUPO 2: CONTATO
        st.markdown("##### 2. Contato")
        c_tel, c_zap = st.columns(2)
        n_tel = c_tel.text_input("Telefone Fixo")
        n_zap = c_zap.text_input("WhatsApp *")
        
        # GRUPO 3: ENDEREÇO (COM CEP AUTOMÁTICO)
        st.markdown("##### 3. Endereço")
        
        # Layout para busca de CEP
        c_cep_in, c_cep_btn = st.columns([3, 1])
        cep_digitado = c_cep_in.text_input("CEP (Somente números)", key="input_cep_novo")
        
        # Variáveis de estado para preencher os campos automaticamente
        if 'end_auto' not in st.session_state:
            st.session_state.end_auto = {}

        # Botão de busca de CEP (fora do form para funcionar dinamicamente seria ideal, 
        # mas dentro do form precisa de submit. Vamos usar um botão "fake" de submit para atualizar)
        if c_cep_btn.form_submit_button("🔍 Buscar CEP"):
            dados_cep = busca_cep_api(cep_digitado)
            if dados_cep:
                st.session_state.end_auto = dados_cep
                st.success("Endereço encontrado!")
            else:
                st.error("CEP não encontrado.")
        
        # Pega valores do estado ou vazio
        val_rua = st.session_state.end_auto.get("logradouro", "")
        val_bairro = st.session_state.end_auto.get("bairro", "")
        val_cidade = st.session_state.end_auto.get("localidade", "")
        val_uf = st.session_state.end_auto.get("uf", "")
        val_pais = st.session_state.end_auto.get("pais", "Brasil")
        
        c_rua, c_num = st.columns([3, 1])
        n_rua = c_rua.text_input("Rua / Logradouro", value=val_rua)
        n_num = c_num.text_input("Número")
        
        c_bairro, c_mun = st.columns(2)
        n_bairro = c_bairro.text_input("Bairro", value=val_bairro)
        n_mun = c_mun.text_input("Município", value=val_cidade)
        
        c_uf, c_pais = st.columns(2)
        n_uf = c_uf.text_input("Estado (UF)", value=val_uf)
        n_pais = c_pais.text_input("País", value=val_pais)
        
        st.markdown("---")
        
        if st.form_submit_button("✅ SALVAR CADASTRO", type="primary"):
            if n_nome and n_zap:
                novo_id = 1
                if clientes:
                    novo_id = max([c['id'] for c in clientes]) + 1
                
                novo_cliente = {
                    "id": novo_id,
                    "nome": n_nome,
                    "cpf": n_cpf,
                    "rg": n_rg,
                    "nascimento": n_nasc.strftime("%Y-%m-%d"),
                    "contato": {
                        "telefone": n_tel,
                        "whatsapp": n_zap
                    },
                    "endereco": {
                        "cep": cep_digitado,
                        "logradouro": n_rua,
                        "numero": n_num,
                        "bairro": n_bairro,
                        "municipio": n_mun,
                        "estado": n_uf,
                        "pais": n_pais
                    },
                    "historico_vendas": [],
                    "receitas": []
                }
                
                clientes.append(novo_cliente)
                salvar_dados(clientes)
                
                # Limpa estado do CEP
                st.session_state.end_auto = {}
                st.success(f"Cliente {n_nome} cadastrado com sucesso!")
                st.rerun()
            else:
                st.warning("Preencha pelo menos o Nome e o WhatsApp.")