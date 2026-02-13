# ARQUIVO: pages/1_Dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.dados import carregar_dados, carregar_produtos
from modules.ui import configurar_pagina_padrao # Visual novo

# Aplica o visual vermelho
configurar_pagina_padrao()

st.title("📊 Painel Gerencial")

# 1. CARREGAMENTO DE DADOS
clientes = carregar_dados()
produtos = carregar_produtos()

# --- CÁLCULOS ---
total_clientes = len(clientes)
total_vendido = 0.0
qtde_vendas = 0
todas_vendas = []

for c in clientes:
    historico = c.get("historico_vendas", [])
    for venda in historico:
        total_vendido += venda["valor_total"]
        qtde_vendas += 1
        todas_vendas.append({
            "Data": venda["data"],
            "Cliente": c["nome"],
            "Valor": venda["valor_total"]
        })

ticket_medio = total_vendido / qtde_vendas if qtde_vendas > 0 else 0

total_itens_estoque = 0
valor_estoque = 0.0
alerta_estoque_baixo = []

if produtos:
    for p in produtos:
        total_itens_estoque += p['quantidade']
        valor_estoque += (p['quantidade'] * p['preco'])
        if p['quantidade'] < 5:
            alerta_estoque_baixo.append(p)

# --- EXIBIÇÃO ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento Total", f"R$ {total_vendido:,.2f}")
col2.metric("Vendas Realizadas", qtde_vendas)
col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
col4.metric("Valor em Estoque", f"R$ {valor_estoque:,.2f}")

st.markdown("---")

c_graf1, c_graf2 = st.columns([2, 1])

with c_graf1:
    st.subheader("📈 Evolução de Vendas")
    if todas_vendas:
        df_vendas = pd.DataFrame(todas_vendas)
        try:
            # Tenta converter data com hora ou sem hora
            df_vendas["Data"] = pd.to_datetime(df_vendas["Data"], dayfirst=True, format="mixed")
        except:
            pass
        
        if "Data" in df_vendas.columns:
            vendas_por_dia = df_vendas.groupby(df_vendas["Data"].dt.date)["Valor"].sum().reset_index()
            fig = px.line(vendas_por_dia, x="Data", y="Valor", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Realize vendas para ver o gráfico.")

with c_graf2:
    st.subheader("🛒 Estoque por Tipo")
    if produtos:
        df_prod = pd.DataFrame(produtos)
        estoque_cat = df_prod.groupby("tipo")["quantidade"].sum().reset_index()
        fig2 = px.pie(estoque_cat, values='quantidade', names='tipo', hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Cadastre produtos.")

# --- ALERTAS ---
st.divider()
c_alert1, c_alert2 = st.columns(2)

with c_alert1:
    st.subheader("⚠️ Estoque Baixo")
    if alerta_estoque_baixo:
        df_baixo = pd.DataFrame(alerta_estoque_baixo)
        st.dataframe(df_baixo[["nome", "quantidade"]], use_container_width=True, hide_index=True)
    else:
        st.success("Estoque saudável.")

with c_alert2:
    st.subheader("🩺 Receitas Vencidas")
    vencidos = []
    hoje = datetime.now()
    for c in clientes:
        rx = c.get("receitas", [])
        if rx:
            try:
                # Tenta formatos variados de data para não quebrar
                dt_str = rx[-1]["data"]
                if "-" in dt_str: dt_rx = datetime.strptime(dt_str, "%Y-%m-%d")
                else: dt_rx = datetime.strptime(dt_str, "%d/%m/%Y")
                
                if (hoje - dt_rx).days > 365:
                    vencidos.append({"Cliente": c["nome"], "WhatsApp": c["contato"].get("whatsapp")})
            except:
                pass
    if vencidos:
        st.dataframe(pd.DataFrame(vencidos), use_container_width=True)
    else:
        st.success("Nenhuma receita vencida.")