import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.charts import grafico_status_ativos
import pandas as pd

st.set_page_config(page_title="Navegacao pela Planta", page_icon="🗺️", layout="wide")
st.title("Navegacao pela Planta Industrial")
st.markdown("Hierarquia: **Planta → Area → Ativo**")
st.divider()

plantas = db.get_plantas()
col_nav, col_detail = st.columns([1, 2])

with col_nav:
    st.subheader("Hierarquia")
    planta_sel = st.selectbox("Planta", plantas, format_func=lambda p: p["nome"])
    areas = db.get_areas(planta_sel["id"]) if planta_sel else []
    area_sel = st.selectbox("Area", [None] + areas,
                            format_func=lambda a: "— Todas as areas —" if a is None else a["nome"])

    if area_sel:
        ativos = db.get_ativos(area_id=area_sel["id"])
    else:
        ativos = []
        for ar in areas:
            ativos.extend(db.get_ativos(area_id=ar["id"]))

    ativo_sel = st.selectbox("Ativo", [None] + ativos,
                             format_func=lambda a: "— Todos —" if a is None
                             else f"{a['codigo']} — {a['descricao']}")

with col_detail:
    if ativo_sel:
        a = ativo_sel
        cor = {"ativo": "🟢", "manutencao": "🟡", "inativo": "🔴"}
        st.subheader(f"{a['codigo']} — {a['descricao']}")
        st.markdown(f"**Status:** {cor.get(a['status'], '⚪')} {a['status'].upper()}")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Identificacao**")
            st.markdown(f"- **Codigo:** `{a['codigo']}`")
            st.markdown(f"- **TAG:** `{a.get('tag') or 'Nao definida'}`")
            st.markdown(f"- **Fabricante:** {a.get('fabricante') or '-'}")
            st.markdown(f"- **Instalacao:** {a.get('data_install') or '-'}")
        with col2:
            st.markdown("**Dados da Placa**")
            st.markdown(f"- **Potencia:** {a.get('potencia_kw') or '-'} kW")
            st.markdown(f"- **Tensao:** {a.get('tensao_v') or '-'} V")
            st.markdown(f"- **Corrente Nom.:** {a.get('corrente_nom') or '-'} A")
            st.markdown(f"- **Protecao:** {a.get('ip_rating') or '-'}")

        st.divider()
        localizacao = a.get("localizacao_descricao") or a.get("localizacao") or "Nao definida"
        st.markdown(f"**Localizacao:** {localizacao}")
        st.markdown(f"**Planta:** {a.get('planta_nome') or '-'} | **Area:** {a.get('area_nome') or '-'}")

        if a.get("latitude") and a.get("longitude"):
            st.map(pd.DataFrame([{"lat": a["latitude"], "lon": a["longitude"]}]), zoom=15)

        st.session_state["ativo_codigo_sel"] = a["codigo"]
        if st.button("Ver Dashboard", type="primary"):
            st.info("Acesse a pagina 'Dashboard do Ativo' no menu lateral.")

    else:
        st.subheader(f"Resumo — {planta_sel['nome'] if planta_sel else 'Todas'}")
        if ativos:
            st.plotly_chart(grafico_status_ativos(ativos), use_container_width=True)

            df = pd.DataFrame(ativos)[["codigo", "tag", "descricao", "area_nome", "status", "fabricante", "potencia_kw"]]
            df.columns = ["Codigo", "TAG", "Descricao", "Area", "Status", "Fabricante", "Pot.(kW)"]

            icones_st = {"ativo": "🟢 ativo", "manutencao": "🟡 manutencao", "inativo": "🔴 inativo"}
            df["Status"] = df["Status"].map(lambda v: icones_st.get(v, v))
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum ativo nesta selecao.")
