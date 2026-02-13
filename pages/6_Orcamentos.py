import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from modules.dados import carregar_dados, salvar_dados, carregar_produtos
from modules.ui import configurar_pagina_padrao

# 1. Aplica o visual padrão (Vermelho/Cinza)
configurar_pagina_padrao()

# --- CSS PARA IMPRESSÃO (IGUAL AO PDV) ---
st.markdown("""
<style>
    @media print {
        [data-testid="stSidebar"], 
        .stAppHeader, 
        .block-container form, 
        .stButton, 
        .no-print {
            display: none !important;
        }
        .cupom-fiscal {
            display: block !important;
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            font-family: 'Courier New', Courier, monospace;
            color: black;
        }
    }
    .cupom-fiscal {
        background-color: #fff;
        padding: 20px;
        border: 1px dashed #333;
        margin-top: 20px;
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("📄 Gerar Orçamento")

# --- FUNÇÕES ---
def busca_cep(cep_input):
    cep_limpo = str(cep_input).replace("-", "").replace(".", "").strip()
    if len(cep_limpo) == 8:
        try:
            r = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
            d = r.json()
            if "erro" not in d: return d
        except: pass
    return None

# --- CARREGAMENTO ---
clientes = carregar_dados()
produtos = carregar_produtos()
usuario_logado = st.session_state.get('usuario_atual', 'Vendedor')

# --- ESTADO (SESSION STATE) ---
if 'orcamento_dados' not in st.session_state: st.session_state.orcamento_dados = {}

# ==================================================
# COLUNA 1: DADOS DO CLIENTE
# ==================================================
col_dados, col_carrinho = st.columns([1, 1.2])

with col_dados:
    st.subheader("1. Dados do Cliente")
    
    # Seleção Rápida
    lista_clientes = ["-- Cliente Novo / Avulso --"] + [f"{c['id']} - {c['nome']}" for c in clientes]
    cli_sel = st.selectbox("Buscar Cliente Cadastrado:", lista_clientes, key="orc_cli_sel")
    
    # Variáveis Padrão
    v_nome, v_cpf, v_rg, v_tel, v_zap = "", "", "", "", ""
    v_cep, v_rua, v_num, v_bairro, v_cidade, v_uf = "", "", "", "", "", ""

    if cli_sel != "-- Cliente Novo / Avulso --":
        id_cli = int(cli_sel.split(" - ")[0])
        c_obj = next(c for c in clientes if c['id'] == id_cli)
        v_nome = c_obj['nome']
        v_cpf = c_obj.get('cpf', '')
        v_rg = c_obj.get('rg', '')
        v_tel = c_obj['contato'].get('telefone', '')
        v_zap = c_obj['contato'].get('whatsapp', '')
        end = c_obj.get('endereco', {})
        v_cep = end.get('cep', '')
        v_rua = end.get('logradouro', '')
        v_num = end.get('numero', '')
        v_bairro = end.get('bairro', '')
        v_cidade = end.get('municipio', '')
        v_uf = end.get('estado', '')

    with st.form("form_orcamento_cli"):
        st.markdown("###### Dados Pessoais")
        i_nome = st.text_input("Nome Completo", value=v_nome)
        c1, c2 = st.columns(2)
        i_cpf = c1.text_input("CPF", value=v_cpf)
        i_rg = c2.text_input("RG", value=v_rg)
        c3, c4 = st.columns(2)
        i_tel = c3.text_input("Telefone", value=v_tel)
        i_zap = c4.text_input("WhatsApp", value=v_zap)
        
        st.markdown("###### Endereço")
        cc1, cc2 = st.columns([2, 1])
        i_cep = cc1.text_input("CEP", value=v_cep)
        if cc2.form_submit_button("🔍 Buscar CEP"):
             d_cep = busca_cep(i_cep)
             if d_cep:
                 v_rua, v_bairro = d_cep.get('logradouro'), d_cep.get('bairro')
                 v_cidade, v_uf = d_cep.get('localidade'), d_cep.get('uf')
                 st.success("Endereço encontrado!")
                 st.rerun()
        
        i_rua = st.text_input("Rua", value=v_rua)
        cn1, cn2 = st.columns([1, 2])
        i_num = cn1.text_input("Número", value=v_num)
        i_bairro = cn2.text_input("Bairro", value=v_bairro)
        ccid, cuf = st.columns([3, 1])
        i_cidade = ccid.text_input("Cidade", value=v_cidade)
        i_uf = cuf.text_input("UF", value=v_uf)
        
        st.markdown("---")
        if st.form_submit_button("Confirmar Dados"):
            st.session_state.orcamento_dados = {
                "nome": i_nome, "cpf": i_cpf, "rg": i_rg, "tel": i_tel, "zap": i_zap,
                "end": f"{i_rua}, {i_num} - {i_bairro}, {i_cidade}/{i_uf} ({i_cep})"
            }
            st.success("Dados preenchidos!")

# ==================================================
# COLUNA 2: ITENS E SIMULAÇÃO
# ==================================================
with col_carrinho:
    st.subheader("2. Itens do Orçamento")
    
    # Mostra todos os produtos (mesmo sem estoque, pois é orçamento, pode ser encomenda)
    lista_display = [f"{p['codigo']} | {p['nome']} (R$ {p['preco']:.2f})" for p in produtos]
    
    itens_selecionados = st.multiselect(
        "Selecione os Produtos:", 
        lista_display, 
        placeholder="Digite o código ou nome..."
    )
    
    total = 0.0
    carrinho_obj = []
    
    if itens_selecionados:
        st.markdown("###### Resumo")
        for item in itens_selecionados:
            cod = item.split(" | ")[0]
            prod = next(p for p in produtos if p['codigo'] == cod)
            total += prod['preco']
            carrinho_obj.append(prod)
        
        # Tabela
        df_cart = pd.DataFrame([{
            "Item": p['nome'],
            "Preço": f"R$ {p['preco']:.2f}"
        } for p in carrinho_obj])
        st.dataframe(df_cart, use_container_width=True, hide_index=True)
        
        st.markdown(f"<h3 style='text-align: right; color: blue;'>Total Estimado: R$ {total:,.2f}</h3>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("3. Simulação de Pagamento")
        
        forma_pag = st.selectbox("Forma de Pagamento Pretendida", 
            ["DINHEIRO", "PIX", "CARTÃO DE DÉBITO", "CARTÃO DE CRÉDITO", "BOLETO", "PARCELAMENTO DIRETO"])
        
        parcelas = 1
        valor_parcela = total
        
        if forma_pag in ["CARTÃO DE CRÉDITO", "PARCELAMENTO DIRETO"]:
            parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=12, value=1)
            valor_parcela = total / parcelas
            st.info(f"Simulação: {parcelas}x de R$ {valor_parcela:,.2f}")
            
        obs = st.text_area("Observações (Ex: Desconto se pagar à vista)")
        
        # BOTÃO GERAR ORÇAMENTO (NÃO BAIXA ESTOQUE)
        if st.button("📄 IMPRIMIR ORÇAMENTO", type="primary", use_container_width=True):
            if not st.session_state.orcamento_dados.get("nome"):
                st.error("Preencha os dados do cliente primeiro.")
            else:
                # 1. SALVAR NO HISTÓRICO (OPCIONAL)
                # Vamos salvar como 'orcamentos' dentro do cliente para não misturar com vendas
                if cli_sel != "-- Cliente Novo / Avulso --":
                    id_cli = int(cli_sel.split(" - ")[0])
                    c_orig = next(c for c in clientes if c['id'] == id_cli)
                    
                    novo_orc = {
                        "data": datetime.now().strftime("%d/%m/%Y"),
                        "itens": [p['nome'] for p in carrinho_obj],
                        "total": total,
                        "tipo": "ORCAMENTO"
                    }
                    if "historico_orcamentos" not in c_orig: c_orig["historico_orcamentos"] = []
                    c_orig["historico_orcamentos"].append(novo_orc)
                    salvar_dados(clientes)
                
                # 2. GERAR DOCUMENTO
                dados = st.session_state.orcamento_dados
                data_hoje = datetime.now()
                validade = data_hoje + timedelta(days=7) # Validade de 7 dias
                
                html_itens = ""
                for p in carrinho_obj:
                    html_itens += f"<tr><td>{p['nome']}</td><td style='text-align:right'>R$ {p['preco']:.2f}</td></tr>"
                
                html_orcamento = f"""
                <div class="cupom-fiscal">
                    <h3 style="text-align:center">ORÇAMENTO - FÁBRICA DE ÓCULOS JR</h3>
                    <p style="text-align:center">Este documento não garante reserva de estoque.</p>
                    <hr>
                    <p><b>EMISSÃO:</b> {data_hoje.strftime("%d/%m/%Y")}</p>
                    <p><b>VÁLIDO ATÉ:</b> {validade.strftime("%d/%m/%Y")}</p>
                    <p><b>CONSULTOR:</b> {usuario_logado}</p>
                    <hr>
                    <p><b>CLIENTE:</b> {dados['nome']}</p>
                    <p><b>CPF:</b> {dados['cpf']} | <b>TEL:</b> {dados['tel']}</p>
                    <p><b>END:</b> {dados['end']}</p>
                    <hr>
                    <table style="width:100%">
                        <tr><th style="text-align:left">ITEM</th><th style="text-align:right">VALOR</th></tr>
                        {html_itens}
                    </table>
                    <hr>
                    <h3 style="text-align:right">TOTAL: R$ {total:,.2f}</h3>
                    <p><b>CONDIÇÃO:</b> {forma_pag} ({parcelas}x)</p>
                    <br>
                    <p style="text-align:center; font-size: 12px;">* Orçamento sujeito a alteração de valores após a validade.</p>
                    <p style="text-align:center; font-size: 12px;">NÃO POSSUI VALOR FISCAL</p>
                </div>
                <br>
                <div class="no-print" style="text-align: center;">
                    <button onclick="window.print()" style="background-color: #007BFF; color: white; padding: 15px 32px; font-size: 16px; border: none; cursor: pointer;">
                        🖨️ IMPRIMIR ORÇAMENTO
                    </button>
                </div>
                """
                
                st.markdown(html_orcamento, unsafe_allow_html=True)