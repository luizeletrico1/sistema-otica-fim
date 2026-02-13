import streamlit as st
import pandas as pd
from modules.dados import carregar_produtos, salvar_produtos
from modules.ui import configurar_pagina_padrao

# 1. Aplica o visual vermelho
configurar_pagina_padrao()

st.title("📦 Almoxarifado & Estoque")

# --- CARREGA DADOS ---
produtos = carregar_produtos()

# --- METRICAS RÁPIDAS ---
if produtos:
    df = pd.DataFrame(produtos)
    c1, c2, c3 = st.columns(3)
    c1.metric("Itens Totais", int(df['quantidade'].sum()))
    c2.metric("Valor em Estoque", f"R$ {(df['quantidade'] * df['preco']).sum():,.2f}")
    c3.metric("SKUs Cadastrados", len(produtos))
    st.markdown("---")

# --- CONTROLE DE ESTADO (EDIÇÃO) ---
if 'prod_edit_id' not in st.session_state:
    st.session_state.prod_edit_id = None

# --- LAYOUT DIVIDIDO ---
col_lista, col_form = st.columns([1.5, 1])

# ==================================================
# COLUNA DA ESQUERDA: LISTA & BUSCA
# ==================================================
with col_lista:
    st.subheader("📋 Lista de Produtos")
    
    filtro = st.text_input("🔍 Buscar por Nome ou Código", placeholder="Ex: Rayban...")
    
    # Filtra a lista
    lista_exibicao = []
    if produtos:
        for p in produtos:
            # Garante que as chaves existem para evitar erro
            p_nome = p.get('nome', '')
            p_cod = p.get('codigo', '')
            
            if filtro.lower() in p_nome.lower() or filtro in p_cod:
                lista_exibicao.append(p)
    
    # Exibe a lista
    if not lista_exibicao:
        st.info("Nenhum produto encontrado.")
    else:
        # Cabeçalho da Tabela Visual
        st.markdown(f"**Encontrados: {len(lista_exibicao)} produtos**")
        
        for i, prod in enumerate(lista_exibicao):
            with st.container(border=True):
                # Layout do Card: [Texto Descrição] [Botão Editar] [Botão Excluir]
                c_txt, c_btn_edit, c_btn_del = st.columns([4, 1, 1])
                
                with c_txt:
                    st.markdown(f"**{prod['nome']}**")
                    st.caption(f"Cod: {prod.get('codigo','-')} | Qtd: {prod['quantidade']} | R$ {prod['preco']:.2f}")
                
                with c_btn_edit:
                    if st.button("✏️", key=f"edit_{prod['id']}", help="Editar este produto"):
                        st.session_state.prod_edit_id = prod['id']
                        st.rerun()
                
                with c_btn_del:
                    if st.button("🗑️", key=f"del_{prod['id']}", help="Excluir este produto"):
                        # Remove da lista original
                        produtos = [p for p in produtos if p['id'] != prod['id']]
                        salvar_produtos(produtos)
                        st.success("Deletado!")
                        st.rerun()

# ==================================================
# COLUNA DA DIREITA: FORMULÁRIO INTELIGENTE
# ==================================================
with col_form:
    # Verifica se estamos em MODO EDIÇÃO ou MODO NOVO
    produto_em_edicao = None
    if st.session_state.prod_edit_id is not None:
        # Tenta achar o produto pelo ID
        matches = [p for p in produtos if p['id'] == st.session_state.prod_edit_id]
        if matches:
            produto_em_edicao = matches[0]
    
    # --- MODO EDIÇÃO ---
    if produto_em_edicao:
        st.subheader(f"✏️ Editando Produto")
        st.info(f"Alterando: {produto_em_edicao['nome']}")
        
        with st.form("form_editar_prod"):
            e_nome = st.text_input("Nome", value=produto_em_edicao['nome'])
            c1, c2 = st.columns(2)
            e_cod = c1.text_input("Código", value=produto_em_edicao.get('codigo',''))
            e_tipo = c2.selectbox("Tipo", ["Armação", "Lente", "Lente Contato", "Acessório"], 
                                  index=["Armação", "Lente", "Lente Contato", "Acessório"].index(produto_em_edicao.get('tipo', 'Armação')) if produto_em_edicao.get('tipo') in ["Armação", "Lente", "Lente Contato", "Acessório"] else 0)
            
            c3, c4 = st.columns(2)
            e_qtd = c3.number_input("Quantidade", value=int(produto_em_edicao['quantidade']), step=1)
            e_preco = c4.number_input("Preço (R$)", value=float(produto_em_edicao['preco']), step=10.0)
            
            e_marca = st.text_input("Marca", value=produto_em_edicao.get('marca', ''))
            
            col_save, col_cancel = st.columns(2)
            
            if col_save.form_submit_button("💾 Salvar Alterações", type="primary"):
                # Atualiza os dados na lista original
                idx = produtos.index(produto_em_edicao)
                produtos[idx]['nome'] = e_nome
                produtos[idx]['codigo'] = e_cod
                produtos[idx]['tipo'] = e_tipo
                produtos[idx]['quantidade'] = e_qtd
                produtos[idx]['preco'] = e_preco
                produtos[idx]['marca'] = e_marca
                
                salvar_produtos(produtos)
                st.session_state.prod_edit_id = None # Sai do modo edição
                st.success("Produto atualizado!")
                st.rerun()
            
            if col_cancel.form_submit_button("❌ Cancelar"):
                st.session_state.prod_edit_id = None
                st.rerun()

    # --- MODO NOVO CADASTRO ---
    else:
        st.subheader("✨ Cadastrar Novo")
        with st.form("form_novo_prod"):
            n_nome = st.text_input("Nome do Produto")
            c1, c2 = st.columns(2)
            n_cod = c1.text_input("Código / SKU")
            n_tipo = c2.selectbox("Tipo", ["Armação", "Lente", "Lente Contato", "Acessório"])
            
            c3, c4 = st.columns(2)
            n_qtd = c3.number_input("Estoque Inicial", min_value=1, value=10)
            n_preco = c4.number_input("Preço de Venda (R$)", min_value=0.0)
            
            n_marca = st.text_input("Marca / Fabricante")
            
            if st.form_submit_button("Cadastrar Produto"):
                if n_nome and n_cod:
                    # Gera um ID novo baseado no maior ID existente
                    novo_id = 1000
                    if produtos:
                        novo_id = max([p['id'] for p in produtos]) + 1
                    
                    novo_prod = {
                        "id": novo_id,
                        "nome": n_nome,
                        "codigo": n_cod,
                        "tipo": n_tipo,
                        "quantidade": n_qtd,
                        "preco": n_preco,
                        "marca": n_marca
                    }
                    produtos.append(novo_prod)
                    salvar_produtos(produtos)
                    st.success(f"{n_nome} cadastrado!")
                    st.rerun()
                else:
                    st.warning("Preencha Nome e Código pelo menos.")