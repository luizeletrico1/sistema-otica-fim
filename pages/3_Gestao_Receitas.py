import streamlit as st
import pandas as pd
from datetime import datetime, date
from modules.dados import carregar_dados, salvar_dados
from modules.ui import configurar_pagina_padrao

configurar_pagina_padrao()

st.title("🩺 Gestão Clínica & Receituário")

clientes = carregar_dados()
if not clientes:
    st.error("Cadastre clientes primeiro.")
    st.stop()

def calcular_idade(data_str):
    if not data_str: return "?"
    try: nasc = datetime.strptime(data_str, "%d/%m/%Y").date()
    except: 
        try: nasc = datetime.strptime(data_str, "%Y-%m-%d").date()
        except: return "?"
    hoje = date.today()
    return hoje.year - nasc.year - ((hoje.month, hoje.day) < (nasc.month, nasc.day))

aba_nova, aba_crm = st.tabs(["📝 Nova Receita", "🔔 CRM Vencimentos"])

with aba_nova:
    lista_pacientes = [f"{c['id']} - {c['nome']}" for c in clientes]
    paciente_sel = st.selectbox("Selecione o Paciente:", lista_pacientes)
    cliente_obj = next(c for c in clientes if c['id'] == int(paciente_sel.split(" - ")[0]))
    
    st.info(f"Paciente: **{cliente_obj['nome']}** | Idade: {calcular_idade(cliente_obj.get('nascimento',''))} anos")
    
    with st.form("form_receita"):
        data_exame = st.date_input("Data do Exame", format="DD/MM/YYYY")
        medico = st.text_input("Médico Responsável")
        
        st.markdown("### 👓 Dioptria")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Olho Direito**")
            esf_od = st.number_input("Esf OD", step=0.25)
            cil_od = st.number_input("Cil OD", step=0.25)
            eixo_od = st.number_input("Eixo OD", step=1)
        with c2:
            st.markdown("**Olho Esquerdo**")
            esf_oe = st.number_input("Esf OE", step=0.25)
            cil_oe = st.number_input("Cil OE", step=0.25)
            eixo_oe = st.number_input("Eixo OE", step=1)
            
        adicao = st.number_input("Adição", step=0.25)
        obs = st.text_area("Obs")
        
        if st.form_submit_button("💾 Salvar"):
            nova_receita = {
                "data": data_exame.strftime("%d/%m/%Y"),
                "medico": medico,
                "od": {"esf": esf_od, "cil": cil_od, "eixo": eixo_od},
                "oe": {"esf": esf_oe, "cil": cil_oe, "eixo": eixo_oe},
                "adicao": adicao, "obs": obs
            }
            if "receitas" not in cliente_obj: cliente_obj["receitas"] = []
            cliente_obj["receitas"].append(nova_receita)
            salvar_dados(clientes)
            st.success("Salvo!")

    st.divider()
    if "receitas" in cliente_obj and cliente_obj["receitas"]:
        st.write("Histórico:")
        for rx in reversed(cliente_obj["receitas"]):
            st.text(f"📅 {rx['data']} - Dr. {rx.get('medico','-')}")

with aba_crm:
    st.subheader("🔔 Vencimentos (> 1 ano)")
    vencidos = []
    hoje = datetime.now()
    for c in clientes:
        if c.get("receitas"):
            try:
                dt_str = c["receitas"][-1]["data"]
                if "/" in dt_str: dt_rx = datetime.strptime(dt_str, "%d/%m/%Y")
                else: dt_rx = datetime.strptime(dt_str, "%Y-%m-%d")
                
                if (hoje - dt_rx).days > 365:
                    vencidos.append({"Cliente": c["nome"], "WhatsApp": c["contato"]["whatsapp"]})
            except: pass
            
    if vencidos: st.dataframe(pd.DataFrame(vencidos), use_container_width=True)
    else: st.success("Tudo em dia!")