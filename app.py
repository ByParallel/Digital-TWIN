import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import database as db

st.set_page_config(
    page_title="Digital Twin — Planta Industrial",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init ───────────────────────────────────────────────────────────────────────
if "db_initialized" not in st.session_state:
    db.init_db()
    # Populate history if DB has no recent readings
    from utils.mock_data import popular_historico
    ativos = db.get_ativos()
    if ativos:
        leituras = db.get_leituras(ativos[0]["id"], limit=1)
        if not leituras:
            with st.spinner("Gerando historico de sensores (48h)..."):
                total = popular_historico(horas=48, intervalo_min=10)
            st.session_state["historico_total"] = total
    st.session_state["db_initialized"] = True

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"]::before {
    content: "Digital Twin\\A Planta Industrial";
    white-space: pre;
    display: block;
    font-size: 1.4rem;
    font-weight: 700;
    color: white;
    padding: 1.2rem 1rem 0.8rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.2);
    margin-bottom: 0.5rem;
    line-height: 1.6;
}
[data-testid="stSidebarNav"] span:first-child {
    font-size: 1rem;
    font-weight: 400;
    opacity: 0.7;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.divider()
    ativos = db.get_ativos()
    st.metric("Ativos monitorados", len(ativos))
    st.metric("Operacionais", sum(1 for a in ativos if a["status"] == "ativo"))

# ── Home ───────────────────────────────────────────────────────────────────────
st.title("Digital Twin — Visualizacao Operacional")
st.markdown("**Sprint 2** | Continuacao da Sprint 1 (coleta/registro) com navegacao, dashboards e automacao RPA.")
st.divider()

# KPIs
plantas = db.get_plantas()
areas   = db.get_areas()
col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Plantas",        len(plantas))
with col2: st.metric("Areas",          len(areas))
with col3: st.metric("Ativos Totais",  len(ativos))
with col4:
    em_manutencao = sum(1 for a in ativos if a["status"] == "manutencao")
    st.metric("Em Manutencao", em_manutencao)

st.divider()

# Asset table
st.subheader("Ativos Cadastrados")

import pandas as pd

col_f1, col_f2 = st.columns(2)
with col_f1:
    planta_opts = ["Todas"] + [p["nome"] for p in plantas]
    planta_f = st.selectbox("Filtrar por Planta", planta_opts)
with col_f2:
    status_f = st.selectbox("Filtrar por Status", ["Todos", "ativo", "manutencao", "inativo"])

filtrados = ativos
if planta_f != "Todas":
    filtrados = [a for a in filtrados if a.get("planta_nome") == planta_f]
if status_f != "Todos":
    filtrados = [a for a in filtrados if a["status"] == status_f]

if filtrados:
    df = pd.DataFrame(filtrados)[[
        "codigo", "tag", "descricao", "planta_nome", "area_nome",
        "status", "fabricante", "potencia_kw", "tensao_v", "ip_rating"
    ]].rename(columns={
        "codigo": "Codigo", "tag": "TAG", "descricao": "Descricao",
        "planta_nome": "Planta", "area_nome": "Area", "status": "Status",
        "fabricante": "Fabricante", "potencia_kw": "Pot.(kW)",
        "tensao_v": "Tensao(V)", "ip_rating": "IP"
    })

    icones_st = {"ativo": "🟢 ativo", "manutencao": "🟡 manutencao", "inativo": "🔴 inativo"}
    df["Status"] = df["Status"].map(lambda v: icones_st.get(v, v))
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum ativo encontrado.")

# Sprint continuity info
st.divider()
with st.expander("Continuidade com Sprint 1"):
    st.markdown("""
**Base herdada da Sprint 1 (motores.db):**
- Schema: `ativos`, `leituras`, `historico_atualizacoes`, `log_execucoes`
- 3 ativos reais: MTR-001, MTR-002, MTR-003
- +12.000 leituras historicas com deteccao de anomalias
- Hash SHA-256 para idempotencia de insercoes

**Adicionado na Sprint 2:**
- Tabelas `plantas` e `areas` para hierarquia de navegacao
- Colunas `tag`, `area_id`, `latitude`, `longitude`, `localizacao_descricao` em `ativos`
- Interface Streamlit com dashboards e gauges
- RPA de associacao TAG/Localizacao (escreve em `log_execucoes`)
- Pipeline Placa -> OCR -> Cadastro
    """)
