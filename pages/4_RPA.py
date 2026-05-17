import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from rpa.tag_association import associar_tag_localidade, sincronizar_todas_tags, atualizar_coordenadas
from rpa.record_updater  import atualizar_status_ativo, coletar_e_salvar_leitura, atualizar_dados_tecnicos
from utils.mock_data import executar_ciclo_coleta
import pandas as pd

st.set_page_config(page_title="Automacoes RPA", page_icon="🤖", layout="wide")
st.title("Central de Automacoes RPA")
st.markdown("Atualizacao de registros e associacoes sem input manual repetitivo. "
            "Todas as operacoes sao registradas em `log_execucoes` (herdado da Sprint 1).")
st.divider()

tab_assoc, tab_status, tab_coleta, tab_logs, tab_auditoria = st.tabs([
    "Associacao TAG/Localizacao",
    "Atualizar Status",
    "Coleta de Leituras",
    "Log de Execucoes",
    "Historico de Auditoria",
])

# ── TAB 1: TAG association ─────────────────────────────────────────────────────
with tab_assoc:
    st.subheader("RPA: Associacao Automatizada TAG → Area → Localizacao")
    st.info("Valida o codigo, confirma a area e registra a associacao automaticamente.")

    col_ind, col_batch = st.columns(2)

    with col_ind:
        st.markdown("**Associacao Individual**")
        ativos = db.get_ativos()
        codigo_s = st.selectbox("Ativo (codigo)", [a["codigo"] for a in ativos], key="assoc_cod")
        areas = db.get_areas()
        area_s = st.selectbox("Nova Area", areas,
                              format_func=lambda a: f"{a['planta_nome']} -> {a['nome']}", key="assoc_area")
        nova_tag = st.text_input("TAG (opcional)", placeholder="MTR-001")
        nova_loc = st.text_input("Descricao de Localizacao", placeholder="Bloco A - Modulo 2")

        if st.button("Executar Associacao RPA", type="primary"):
            with st.spinner("RPA executando..."):
                r = associar_tag_localidade(codigo_s, area_s["id"], nova_loc,
                                            tag=nova_tag or None)
            if r["status"] == "Sucesso":
                st.success(f"OK: {r['mensagem']}")
            elif r["status"] == "Aviso":
                st.warning(r["mensagem"])
            else:
                st.error(r["mensagem"])

        st.divider()
        st.markdown("**Atualizar Coordenadas GPS**")
        cod_gps = st.selectbox("Ativo", [a["codigo"] for a in ativos], key="gps_cod")
        c1, c2 = st.columns(2)
        with c1: lat = st.number_input("Latitude",  value=-23.5505, format="%.6f")
        with c2: lon = st.number_input("Longitude", value=-46.6333, format="%.6f")
        if st.button("Atualizar Coordenadas"):
            r = atualizar_coordenadas(cod_gps, lat, lon)
            (st.success if r["status"] == "Sucesso" else st.error)(r["mensagem"])

    with col_batch:
        st.markdown("**Sincronizacao em Lote**")
        st.markdown("Valida e ressincroniza TODOS os ativos de uma vez.")
        if st.button("Sincronizar Todos (Batch)", type="secondary"):
            with st.spinner("Processando todos os ativos..."):
                resultados = sincronizar_todas_tags()
            ok = sum(1 for r in resultados if r["status"] == "Sucesso")
            st.metric("Sucesso",  ok)
            st.metric("Avisos",   sum(1 for r in resultados if r["status"] == "Aviso"))
            st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)

# ── TAB 2: Status ─────────────────────────────────────────────────────────────
with tab_status:
    st.subheader("RPA: Atualizacao de Status")
    ativos = db.get_ativos()
    col1, col2 = st.columns(2)
    with col1:
        ativo_st = st.selectbox("Ativo", ativos,
                                format_func=lambda a: f"{a['codigo']} [{a['status']}]")
        novo_st  = st.selectbox("Novo Status", ["ativo","manutencao","inativo","em_teste"])
        if st.button("Atualizar Status", type="primary"):
            r = atualizar_status_ativo(ativo_st["codigo"], novo_st)
            (st.success if r["status"] == "Sucesso" else st.error)(r["mensagem"])
    with col2:
        df_st = pd.DataFrame(ativos)[["codigo","tag","descricao","status"]]
        df_st.columns = ["Codigo","TAG","Descricao","Status"]
        icones_st = {"ativo": "🟢 ativo", "manutencao": "🟡 manutencao", "inativo": "🔴 inativo"}
        df_st["Status"] = df_st["Status"].map(lambda v: icones_st.get(v, v))
        st.dataframe(df_st, use_container_width=True, hide_index=True)

# ── TAB 3: Collection ─────────────────────────────────────────────────────────
with tab_coleta:
    st.subheader("RPA: Coleta de Leituras de Sensores")
    st.markdown("Usa o mesmo `SimuladorSensorIoT` da Sprint 1 (ruido gaussiano + anomalias).")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Coleta Individual**")
        cod_col = st.selectbox("Ativo", [a["codigo"] for a in db.get_ativos()], key="col_cod")
        if st.button("Coletar Leitura Agora", type="primary"):
            with st.spinner("Coletando..."):
                r = coletar_e_salvar_leitura(cod_col)
            if r["status"] == "Sucesso":
                st.success(r["mensagem"])
                l = r["leitura"]
                st.json({
                    "temperatura_c":  l["temperatura_c"],
                    "vibracao_mm_s":  l["vibracao_mm_s"],
                    "corrente_a":     l["corrente_a"],
                    "tensao_v":       l["tensao_v"],
                    "rpm":            l["rpm"],
                    "fator_potencia": l["fator_potencia"],
                    "flag_anomalia":  l["flag_anomalia"],
                })
            else:
                st.error(r["mensagem"])

    with col2:
        st.markdown("**Ciclo Completo (todos os ativos ativos)**")
        if st.button("Executar Ciclo de Coleta", type="secondary"):
            with st.spinner("Coletando leituras para todos os ativos..."):
                resultados = executar_ciclo_coleta()
            ok = sum(1 for r in resultados if r["status"] == "Sucesso")
            st.success(f"{ok}/{len(resultados)} leituras coletadas com sucesso!")
            anomalias = sum(1 for r in resultados if r.get("flag_anomalia") == 1)
            if anomalias:
                st.warning(f"{anomalias} anomalia(s) detectada(s) neste ciclo!")
            st.dataframe(pd.DataFrame(resultados), use_container_width=True, hide_index=True)

# ── TAB 4: Execution Log ───────────────────────────────────────────────────────
with tab_logs:
    st.subheader("Log de Execucoes (log_execucoes — Sprint 1)")
    logs = db.get_log_execucoes(limit=100)
    if logs:
        df_l = pd.DataFrame(logs)[["iniciado_em","automacao","status",
                                   "registros_proc","registros_erro","finalizado_em"]]
        df_l.columns = ["Iniciado","Automacao","Status","Processados","Erros","Finalizado"]
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_status = st.selectbox("Filtrar Status", ["Todos","sucesso","erro","parcial"])
        with col_f2:
            f_auto = st.selectbox("Filtrar Automacao",
                                  ["Todas"] + list(df_l["Automacao"].unique()))
        df_fil = df_l.copy()
        if f_status != "Todos":
            df_fil = df_fil[df_fil["Status"] == f_status]
        if f_auto != "Todas":
            df_fil = df_fil[df_fil["Automacao"] == f_auto]

        icones = {"sucesso": "✅ sucesso", "erro": "❌ erro", "parcial": "⚠️ parcial"}
        df_fil["Status"] = df_fil["Status"].map(lambda v: icones.get(v, v))
        st.dataframe(df_fil, use_container_width=True, hide_index=True)
        st.download_button("Exportar Log",
                           df_fil.to_csv(index=False).encode("utf-8"),
                           "log_execucoes.csv", "text/csv")
    else:
        st.info("Nenhuma execucao registrada.")

# ── TAB 5: Audit history ───────────────────────────────────────────────────────
with tab_auditoria:
    st.subheader("Historico de Auditoria (historico_atualizacoes — Sprint 1)")
    st.info("Cada INSERT/UPDATE em ativos gera um registro com estado antes/depois em JSON.")
    hist = db.get_historico_atualizacoes(limit=50)
    if hist:
        df_h = pd.DataFrame(hist)[["executado_em","tabela","operacao","registro_id","executor"]]
        df_h.columns = ["Executado em","Tabela","Operacao","ID Registro","Executor"]
        st.dataframe(df_h, use_container_width=True, hide_index=True)

        with st.expander("Ver dados antes/depois (JSON)"):
            for h in hist[:5]:
                st.markdown(f"**ID {h['id']} | {h['operacao']} | {h['executado_em']}**")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("Antes:")
                    st.json(h.get("dados_antes") or "{}")
                with c2:
                    st.markdown("Depois:")
                    st.json(h.get("dados_depois") or "{}")
                st.divider()
    else:
        st.info("Sem registros de auditoria.")
