import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from modules.dados import carregar_dados, salvar_dados, carregar_produtos, salvar_produtos
from modules.ui import configurar_pagina_padrao

# 1. Aplica o visual padrão
configurar_pagina_padrao()

# --- CSS PARA IMPRESSÃO (O SEGREDO DO RECIBO) ---
st.markdown("""
<style>
    /* Esconde tudo na hora de imprimir */
    @media print {
        [data-testid="stSidebar"], 
        .stAppHeader, 
        .block-container form, 
        .stButton, 
        .no-print {
            display: none !important;
        }
        /* Mostra só o recibo */
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
    
    /* Estilo do Cupom na Tela */
    .cupom-fiscal {
        background-color: #fff;
        padding: 20px;
        border: 1px dashed #333;
        margin-top: 20px;
        font-family: 'Courier New', Courier, monospace;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 PDV - Frente de Caixa")

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
usuario_logado = st.session_state.get('usuario_atual', 'Vendedor Não Identificado')

if not produtos:
    st.error("⚠️ Cadastre produtos no Estoque antes de vender.")
    st.stop()

# --- INICIALIZAÇÃO DE ESTADO (Para preencher campos automáticos) ---
if 'cliente_selecionado' not in st.session_state: st.session_state.cliente_selecionado = None
if 'dados_venda' not in st.session_state: st.session_state.dados_venda = {}

# ==================================================
# COLUNA 1: DADOS DA VENDA E CARRINHO
# ==================================================
col_dados, col_carrinho = st.columns([1, 1.2])

with col_dados:
    st.subheader("1. Identificação do Cliente")
    
    # Seleção Rápida
    lista_clientes = ["-- Venda Avulsa --"] + [f"{c['id']} - {c['nome']}" for c in clientes]
    cli_sel = st.selectbox("Buscar Cliente Cadastrado:", lista_clientes)
    
    # Variáveis para o formulário
    v_nome, v_cpf, v_rg, v_tel, v_zap = "", "", "", "", ""
    v_cep, v_rua, v_num, v_bairro, v_cidade, v_uf = "", "", "", "", "", ""

    # Se selecionou alguém, preenche as variáveis
    if cli_sel != "-- Venda Avulsa --":
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

    with st.form("form_dados_cliente"):
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
                 st.success("Endereço encontrado! Preencha o número.")
                 st.rerun() # Recarrega para mostrar os dados (limitação do form)
        
        i_rua = st.text_input("Rua", value=v_rua)
        cn1, cn2 = st.columns([1, 2])
        i_num = cn1.text_input("Número", value=v_num)
        i_bairro = cn2.text_input("Bairro", value=v_bairro)
        ccid, cuf = st.columns([3, 1])
        i_cidade = ccid.text_input("Cidade", value=v_cidade)
        i_uf = cuf.text_input("UF", value=v_uf)
        
        st.markdown("---")
        submit_dados = st.form_submit_button("Confirmar Dados do Cliente")
        
        if submit_dados:
            st.session_state.dados_venda = {
                "nome": i_nome, "cpf": i_cpf, "rg": i_rg, "tel": i_tel, "zap": i_zap,
                "end": f"{i_rua}, {i_num} - {i_bairro}, {i_cidade}/{i_uf} ({i_cep})"
            }
            st.success("Dados confirmados!")

# ==================================================
# COLUNA 2: CARRINHO E PAGAMENTO
# ==================================================
with col_carrinho:
    st.subheader("2. Carrinho de Compras")
    
    # Filtra produtos com estoque
    prods_ok = [p for p in produtos if p['quantidade'] > 0]
    # Cria lista bonita para o select
    lista_display = [f"{p['codigo']} | {p['nome']} (R$ {p['preco']:.2f})" for p in prods_ok]
    
    itens_selecionados = st.multiselect(
        "Adicionar Produtos:", 
        lista_display, 
        placeholder="Clique para selecionar ou digite o código..."
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
        
        # Tabela Simples
        df_cart = pd.DataFrame([{
            "Item": p['nome'],
            "Preço": f"R$ {p['preco']:.2f}"
        } for p in carrinho_obj])
        st.dataframe(df_cart, use_container_width=True, hide_index=True)
        
        st.markdown(f"<h3 style='text-align: right; color: green;'>Total: R$ {total:,.2f}</h3>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("3. Pagamento")
        
        forma_pag = st.selectbox("Forma de Pagamento", 
            ["DINHEIRO", "PIX", "CARTÃO DE DÉBITO", "CARTÃO DE CRÉDITO", "BOLETO", "PARCELAMENTO DIRETO"])
        
        parcelas = 1
        valor_parcela = total
        
        if forma_pag in ["CARTÃO DE CRÉDITO", "PARCELAMENTO DIRETO"]:
            parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=12, value=1)
            valor_parcela = total / parcelas
            st.info(f"Previsão: {parcelas}x de R$ {valor_parcela:,.2f}")
            
        obs = st.text_area("Observações da Venda")
        
        # BOTÃO FINALIZAR
        if st.button("✅ FINALIZAR VENDA E GERAR RECIBO", type="primary", use_container_width=True):
            if not st.session_state.dados_venda.get("nome"):
                st.error("Por favor, confirme os dados do cliente no formulário à esquerda antes de finalizar.")
            else:
                # 1. BAIXA DE ESTOQUE
                for item in carrinho_obj:
                    p_orig = next(p for p in produtos if p['id'] == item['id'])
                    p_orig['quantidade'] -= 1
                salvar_produtos(produtos)
                
                # 2. SALVAR NO HISTÓRICO DO CLIENTE (Se for cadastrado)
                # Se for venda avulsa, não salvamos no histórico individual, mas poderíamos ter um arquivo geral de vendas.
                if cli_sel != "-- Venda Avulsa --":
                    id_cli = int(cli_sel.split(" - ")[0])
                    c_orig = next(c for c in clientes if c['id'] == id_cli)
                    
                    nova_venda = {
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "itens": [p['nome'] for p in carrinho_obj],
                        "total": total,
                        "pagamento": f"{forma_pag} ({parcelas}x)",
                        "vendedor": usuario_logado
                    }
                    if "historico_vendas" not in c_orig: c_orig["historico_vendas"] = []
                    c_orig["historico_vendas"].append(nova_venda)
                    salvar_dados(clientes)
                
                # 3. GERAÇÃO DO RECIBO
                dados = st.session_state.dados_venda
                data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                
                # Monta lista de itens para o HTML
                html_itens = ""
                for p in carrinho_obj:
                    html_itens += f"<tr><td>{p['nome']}</td><td style='text-align:right'>R$ {p['preco']:.2f}</td></tr>"
                
                # HTML DO CUPOM
                html_cupom = f"""
                <div class="cupom-fiscal">
                    <h3 style="text-align:center">FÁBRICA DE ÓCULOS JR VITÓRIA</h3>
                    <p style="text-align:center">Vitória - ES | Tel: (27) 99999-9999</p>
                    <hr>
                    <p><b>VENDA Nº:</b> {int(datetime.now().timestamp())}</p>
                    <p><b>DATA:</b> {data_hoje}</p>
                    <p><b>VENDEDOR:</b> {usuario_logado}</p>
                    <hr>
                    <p><b>CLIENTE:</b> {dados['nome']}</p>
                    <p><b>CPF:</b> {dados['cpf']} | <b>RG:</b> {dados['rg']}</p>
                    <p><b>TEL:</b> {dados['tel']} / {dados['zap']}</p>
                    <p><b>END:</b> {dados['end']}</p>
                    <hr>
                    <table style="width:100%">
                        <tr><th style="text-align:left">ITEM</th><th style="text-align:right">VALOR</th></tr>
                        {html_itens}
                    </table>
                    <hr>
                    <h3 style="text-align:right">TOTAL: R$ {total:,.2f}</h3>
                    <p><b>FORMA PAGTO:</b> {forma_pag}</p>
                    <p><b>PARCELAS:</b> {parcelas}x de R$ {valor_parcela:,.2f}</p>
                    <br>
                    <p style="text-align:center"><i>Obrigado pela preferência!</i></p>
                </div>
                <br>
                <div class="no-print" style="text-align: center;">
                    <button onclick="window.print()" style="background-color: #4CAF50; color: white; padding: 15px 32px; font-size: 16px; border: none; cursor: pointer;">
                        🖨️ CLIQUE AQUI PARA IMPRIMIR
                    </button>
                    <p style="color: red; font-size: 12px; margin-top: 5px;">(Na janela de impressão, o menu sumirá automaticamente)</p>
                </div>
                """
                
                # Exibe o cupom
                st.markdown(html_cupom, unsafe_allow_html=True)
                st.balloons()