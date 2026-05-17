import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.mock_data import simular_leitura_atual
from utils.charts import gauge_card, grafico_historico, grafico_multi_sensor, grafico_anomalias
import pandas as pd
import time

st.set_page_config(page_title="Dashboard do Ativo", page_icon="📊", layout="wide")
st.title("Dashboard Operacional — Sensores em Tempo Real")
st.divider()

ativos = db.get_ativos()
codigo_default = st.session_state.get("ativo_codigo_sel", ativos[0]["codigo"] if ativos else None)
codigos = [a["codigo"] for a in ativos]

col_sel, col_auto = st.columns([3, 1])
with col_sel:
    idx = codigos.index(codigo_default) if codigo_default in codigos else 0
    codigo_sel = st.selectbox("Selecione o Ativo", codigos, index=idx)
with col_auto:
    auto = st.toggle("Atualizacao automatica", value=False)
    intervalo = st.slider("Intervalo (s)", 5, 60, 10) if auto else 10

ativo = next((a for a in ativos if a["codigo"] == codigo_sel), None)
if not ativo:
    st.error("Ativo nao encontrado.")
    st.stop()

st.session_state["ativo_codigo_sel"] = codigo_sel

# Header
cor = {"ativo": "🟢", "manutencao": "🟡", "inativo": "🔴"}
localizacao = ativo.get("localizacao_descricao") or ativo.get("localizacao") or "—"
st.markdown(
    f"### {cor.get(ativo['status'],'⚪')} `{ativo['codigo']}` | TAG: `{ativo.get('tag') or 'N/D'}`  \n"
    f"{ativo['descricao']} | {localizacao}  \n"
    f"**Planta:** {ativo.get('planta_nome') or '—'} / {ativo.get('area_nome') or '—'}"
)
st.divider()

# ── Live reading ───────────────────────────────────────────────────────────────
leitura = simular_leitura_atual(ativo)

st.subheader("Valores Atuais (tempo real)")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    alerta_t = leitura["temperatura_c"] > 85
    st.metric("Temperatura", f"{leitura['temperatura_c']} °C",
              delta="ALERTA" if alerta_t else "Normal",
              delta_color="inverse" if alerta_t else "normal")
with col2:
    st.metric("Tensao", f"{leitura['tensao_v']} V")
with col3:
    corrente_lim = (ativo.get("corrente_nom") or 100) * 1.25
    alerta_i = leitura["corrente_a"] > corrente_lim
    st.metric("Corrente", f"{leitura['corrente_a']} A",
              delta="ALERTA" if alerta_i else "Normal",
              delta_color="inverse" if alerta_i else "normal")
with col4:
    st.metric("Rotacao", f"{leitura['rpm']:.0f} RPM")
with col5:
    alerta_v = leitura["vibracao_mm_s"] > 6.0
    st.metric("Vibracao", f"{leitura['vibracao_mm_s']} mm/s",
              delta="ALERTA" if alerta_v else "Normal",
              delta_color="inverse" if alerta_v else "normal")

col6, col7 = st.columns(2)
with col6: st.metric("Fator de Potencia", f"{leitura['fator_potencia']}")
with col7:
    flag = leitura.get("flag_anomalia", 0)
    st.metric("Anomalia Detectada", "SIM" if flag else "NAO",
              delta="ATENCAO" if flag else None,
              delta_color="inverse" if flag else "normal")

# ── Gauges ─────────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Gauges")
gc1, gc2, gc3, gc4 = st.columns(4)
corrente_nom = float(ativo.get("corrente_nom") or 100)
with gc1:
    st.plotly_chart(gauge_card(leitura["temperatura_c"], "Temperatura (C)", 0, 110, alerta=85, cor="#FF5722"), use_container_width=True)
with gc2:
    st.plotly_chart(gauge_card(leitura["corrente_a"], "Corrente (A)", 0, corrente_nom * 1.5, cor="#2196F3"), use_container_width=True)
with gc3:
    st.plotly_chart(gauge_card(leitura["vibracao_mm_s"], "Vibracao (mm/s)", 0, 12, alerta=6.0, cor="#FF9800"), use_container_width=True)
with gc4:
    st.plotly_chart(gauge_card(leitura["fator_potencia"], "Fator de Potencia", 0, 1, cor="#607D8B"), use_container_width=True)

# ── Historical charts ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Historico de Dados")

col_per, col_sensor = st.columns(2)
with col_per:
    periodo = st.select_slider("Periodo", ["1h", "6h", "12h", "24h", "48h"], value="24h")
with col_sensor:
    sensor = st.selectbox("Sensor", [
        "temperatura_c", "corrente_a", "tensao_v", "rpm", "vibracao_mm_s", "fator_potencia"
    ], format_func=lambda x: {
        "temperatura_c": "Temperatura (C)", "corrente_a": "Corrente (A)",
        "tensao_v": "Tensao (V)", "rpm": "Rotacao (RPM)",
        "vibracao_mm_s": "Vibracao (mm/s)", "fator_potencia": "Fator de Potencia"
    }[x])

limite = {"1h": 6, "6h": 36, "12h": 72, "24h": 144, "48h": 288}
leituras_hist = db.get_leituras(ativo["id"], limit=limite[periodo])

if leituras_hist:
    df = pd.DataFrame(leituras_hist)
    df["coletado_em"] = pd.to_datetime(df["coletado_em"])
    df = df.sort_values("coletado_em")

    tab1, tab2, tab3 = st.tabs(["Sensor Individual", "Multi-sensor", "Anomalias"])
    with tab1:
        st.plotly_chart(grafico_historico(df, sensor), use_container_width=True)
    with tab2:
        st.plotly_chart(
            grafico_multi_sensor(df, ["temperatura_c", "corrente_a", "vibracao_mm_s", "rpm"]),
            use_container_width=True
        )
    with tab3:
        total_anomalias = df["flag_anomalia"].sum()
        st.metric("Anomalias no periodo", int(total_anomalias))
        if total_anomalias > 0:
            st.plotly_chart(grafico_anomalias(df), use_container_width=True)
        else:
            st.success("Nenhuma anomalia detectada no periodo selecionado.")

    with st.expander("Dados brutos"):
        st.dataframe(df[["coletado_em","temperatura_c","corrente_a","tensao_v",
                          "rpm","vibracao_mm_s","fator_potencia","flag_anomalia"]],
                     use_container_width=True)
else:
    st.info("Sem dados historicos. Execute a coleta via RPA.")

if auto:
    st.info(f"Atualizando a cada {intervalo} segundos...")
    time.sleep(intervalo)
    st.rerun()
