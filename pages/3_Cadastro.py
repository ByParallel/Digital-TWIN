import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
import pandas as pd

st.set_page_config(page_title="Cadastro de Ativos", page_icon="📋", layout="wide")
st.title("Cadastro e Gestao de Ativos")
st.divider()

tab_lista, tab_novo, tab_editar = st.tabs(["Lista de Ativos", "Novo Ativo", "Editar Ativo"])

# ── LISTA ─────────────────────────────────────────────────────────────────────
with tab_lista:
    st.subheader("Ativos Cadastrados")
    ativos = db.get_ativos()
    if ativos:
        df = pd.DataFrame(ativos)[[
            "codigo", "tag", "descricao", "planta_nome", "area_nome", "status",
            "fabricante", "potencia_kw", "tensao_v", "corrente_nom",
            "ip_rating", "data_install", "atualizado_em"
        ]].rename(columns={
            "codigo": "Codigo", "tag": "TAG", "descricao": "Descricao",
            "planta_nome": "Planta", "area_nome": "Area", "status": "Status",
            "fabricante": "Fabricante", "potencia_kw": "Pot.(kW)",
            "tensao_v": "Tensao(V)", "corrente_nom": "I Nom.(A)",
            "ip_rating": "IP", "data_install": "Instalacao",
            "atualizado_em": "Atualizado"
        })

        icones_st = {"ativo": "🟢 ativo", "manutencao": "🟡 manutencao", "inativo": "🔴 inativo"}
        df["Status"] = df["Status"].map(lambda v: icones_st.get(v, v))
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Exportar CSV",
                           df.to_csv(index=False).encode("utf-8"),
                           "ativos_digital_twin.csv", "text/csv")

# ── NOVO ──────────────────────────────────────────────────────────────────────
with tab_novo:
    st.subheader("Cadastrar Novo Ativo")
    plantas = db.get_plantas()
    planta_n = st.selectbox("Planta", plantas, format_func=lambda p: p["nome"], key="new_p")
    areas    = db.get_areas(planta_n["id"]) if planta_n else []
    area_n   = st.selectbox("Area", areas, format_func=lambda a: a["nome"], key="new_a")

    col1, col2 = st.columns(2)
    with col1:
        codigo_n = st.text_input("Codigo *", placeholder="MTR-004")
        tag_n    = st.text_input("TAG", placeholder="MTR-004")
        desc_n   = st.text_input("Descricao *", placeholder="Motor Bomba Secundaria")
        fab_n    = st.text_input("Fabricante", placeholder="WEG")
    with col2:
        pot_n   = st.number_input("Potencia (kW)", 0.0, 10000.0, step=0.5)
        tensao_n = st.number_input("Tensao (V)", 0.0, 15000.0, value=380.0, step=10.0)
        corr_n  = st.number_input("Corrente Nominal (A)", 0.0, 5000.0, step=0.5)
        ip_n    = st.selectbox("IP Rating", ["IP44","IP54","IP55","IP65","IP66","IP67"])

    status_n   = st.selectbox("Status", ["ativo", "manutencao", "inativo", "em_teste"])
    loc_n      = st.text_input("Localizacao", placeholder="Bloco A - Sala de Maquinas")
    install_n  = st.date_input("Data de Instalacao")

    if st.button("Cadastrar Ativo", type="primary"):
        if not codigo_n or not desc_n or not area_n:
            st.error("Codigo, Descricao e Area sao obrigatorios.")
        else:
            try:
                db.cadastrar_ativo(
                    area_n["id"], codigo_n, desc_n,
                    tag=tag_n or codigo_n,
                    fabricante=fab_n, potencia_kw=pot_n,
                    tensao_v=tensao_n, corrente_nom=corr_n,
                    ip_rating=ip_n, status=status_n,
                    localizacao=loc_n, localizacao_descricao=loc_n,
                    data_install=str(install_n)
                )
                db.registrar_execucao("cadastro_manual", "sucesso", 1, 0,
                                      {"codigo": codigo_n})
                st.success(f"Ativo `{codigo_n}` cadastrado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# ── EDITAR ────────────────────────────────────────────────────────────────────
with tab_editar:
    st.subheader("Editar Ativo Existente")
    ativos = db.get_ativos()
    ativo_e = st.selectbox("Selecionar", ativos,
                           format_func=lambda a: f"{a['codigo']} — {a['descricao']}")
    if ativo_e:
        a = ativo_e
        col1, col2 = st.columns(2)
        with col1:
            tag_e  = st.text_input("TAG",        value=a.get("tag") or "")
            desc_e = st.text_input("Descricao",  value=a.get("descricao") or "")
            fab_e  = st.text_input("Fabricante", value=a.get("fabricante") or "")
        with col2:
            pot_e  = st.number_input("Potencia (kW)", value=float(a.get("potencia_kw") or 0))
            tensao_e = st.number_input("Tensao (V)", value=float(a.get("tensao_v") or 380))
            corr_e = st.number_input("Corrente Nom. (A)", value=float(a.get("corrente_nom") or 0))

        ip_opts = ["IP44","IP54","IP55","IP65","IP66","IP67"]
        ip_e = st.selectbox("IP Rating", ip_opts,
                            index=ip_opts.index(a["ip_rating"]) if a.get("ip_rating") in ip_opts else 2,
                            key="edit_ip")

        status_opts = ["ativo","manutencao","inativo","em_teste"]
        st_e = st.selectbox("Status", status_opts,
                            index=status_opts.index(a["status"]) if a.get("status") in status_opts else 0,
                            key="edit_status")

        loc_e = st.text_input("Localizacao", value=a.get("localizacao_descricao") or a.get("localizacao") or "")

        if st.button("Salvar Alteracoes", type="primary"):
            db.update_ativo(a["codigo"],
                            tag=tag_e, descricao=desc_e, fabricante=fab_e,
                            potencia_kw=pot_e, tensao_v=tensao_e,
                            corrente_nom=corr_e, ip_rating=ip_e,
                            status=st_e, localizacao=loc_e,
                            localizacao_descricao=loc_e)
            st.success(f"Ativo `{a['codigo']}` atualizado!")
            st.rerun()
