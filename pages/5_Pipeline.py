import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from rpa.nameplate_pipeline import (
    pipeline_placa_para_cadastro, gerar_relatorio_pipeline, extrair_dados_simulados
)

st.set_page_config(page_title="Pipeline de Dados", page_icon="🔗", layout="wide")
st.title("Pipeline de Dados — Placa do Motor -> Cadastro Digital")
st.divider()

# Diagrama do pipeline
st.subheader("Fluxo do Pipeline")
st.markdown("""
```
ETAPA 1          ETAPA 2          ETAPA 3          ETAPA 4          ETAPA 5
Foto da Placa -> OCR             -> Parse          -> Validacao     -> Cadastro/Update
(campo/smartphone)  (pytesseract)    (mapeamento        (PipelineTransf.  (ativos + audit
                                      campos)            Sprint 1)          historico)
```
""")

with st.expander("Mapeamento Placa -> Campo no Banco (Sprint 1)"):
    st.markdown("""
| Campo na Placa | Campo em `ativos` (Sprint 1) |
|---|---|
| Fabricante / Manufacturer | `fabricante` |
| Modelo / Frame | `descricao` |
| Corrente / In / Amp | `corrente_nom` |
| Potencia / kW / HP | `potencia_kw` |
| Tensao / V | `tensao_v` |
| Protecao / IP | `ip_rating` |
    """)

st.divider()
tab_exec, tab_mapa, tab_sim = st.tabs(["Executar Pipeline", "Mapeamento Ativo-TAG-Local", "Simulacao OCR"])

# ── Executar ──────────────────────────────────────────────────────────────────
with tab_exec:
    st.subheader("Executar Pipeline de Integracao")
    ativos = db.get_ativos()
    areas  = db.get_areas()

    col1, col2 = st.columns(2)
    with col1:
        cod_pip = st.selectbox("Ativo (codigo)", [a["codigo"] for a in ativos], key="pip_cod")
        area_pip = st.selectbox("Area", areas,
                                format_func=lambda a: f"{a['planta_nome']} -> {a['nome']}", key="pip_area")
    with col2:
        imagem = st.file_uploader("Imagem da Placa (JPG/PNG)",
                                  type=["jpg","jpeg","png","webp"],
                                  help="Sem imagem: usa dados simulados para demo.")
        if imagem:
            st.image(imagem, caption="Imagem carregada", use_column_width=True)

    if st.button("Executar Pipeline Completo", type="primary"):
        img_path = None
        if imagem:
            img_path = os.path.join("data", f"temp_{imagem.name}")
            with open(img_path, "wb") as f:
                f.write(imagem.read())

        with st.spinner("Pipeline executando..."):
            resultado = pipeline_placa_para_cadastro(cod_pip, area_pip["id"], img_path)

        if resultado["status"] == "Sucesso":
            st.success(resultado["mensagem"])
        else:
            st.error(resultado["mensagem"])

        st.markdown("**Etapas executadas:**")
        for e in resultado.get("etapas", []):
            st.markdown(f"- {e}")

        if resultado.get("dados_extraidos"):
            st.markdown("**Dados extraidos da placa:**")
            st.json(resultado["dados_extraidos"])

        relatorio = gerar_relatorio_pipeline([resultado])
        st.download_button("Baixar Relatorio", relatorio, "relatorio_pipeline.txt")

# ── Mapeamento ────────────────────────────────────────────────────────────────
with tab_mapa:
    st.subheader("Mapeamento: Ativo -> TAG -> Localizacao -> Planta")
    st.markdown("Documento tecnico de rastreabilidade para o Digital Twin.")

    import pandas as pd
    ativos = db.get_ativos()
    df_map = pd.DataFrame(ativos)[[
        "codigo","tag","descricao","planta_nome","area_nome",
        "localizacao_descricao","latitude","longitude",
        "fabricante","corrente_nom","ip_rating","status","atualizado_em"
    ]].rename(columns={
        "codigo":"Codigo","tag":"TAG","descricao":"Descricao",
        "planta_nome":"Planta","area_nome":"Area",
        "localizacao_descricao":"Localizacao","latitude":"Lat","longitude":"Lon",
        "fabricante":"Fabricante","corrente_nom":"I.Nom.(A)",
        "ip_rating":"IP","status":"Status","atualizado_em":"Atualizado"
    })
    st.dataframe(df_map, use_container_width=True, hide_index=True)

    df_coords = df_map.dropna(subset=["Lat","Lon"])[["Lat","Lon"]].copy()
    df_coords.columns = ["lat","lon"]
    if not df_coords.empty:
        st.subheader("Mapa de Localizacao dos Ativos")
        st.map(df_coords, zoom=13)

    st.download_button("Exportar Mapeamento (CSV)",
                       df_map.to_csv(index=False).encode("utf-8"),
                       "mapeamento_ativo_tag.csv","text/csv")

# ── Simulacao OCR ─────────────────────────────────────────────────────────────
with tab_sim:
    st.subheader("Simulacao de Extracao OCR")
    st.info("Demonstra como os dados da placa sao interpretados e mapeados para o schema Sprint 1.")
    ativos = db.get_ativos()
    cod_sim = st.selectbox("Ativo", [a["codigo"] for a in ativos], key="sim_cod")

    if st.button("Simular Extracao OCR"):
        with st.spinner("Simulando OCR..."):
            dados = extrair_dados_simulados(cod_sim)

        st.success("Dados extraidos da placa com sucesso!")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Campos extraidos -> banco de dados:**")
            mapeamento = {
                "fabricante (placa)": "-> ativos.fabricante",
                "corrente nominal (placa)": "-> ativos.corrente_nom",
                "potencia kW (placa)": "-> ativos.potencia_kw",
                "tensao V (placa)": "-> ativos.tensao_v",
                "protecao IP (placa)": "-> ativos.ip_rating",
            }
            for k, v in mapeamento.items():
                st.markdown(f"- `{k}` **{v}**")
            st.markdown("---")
            st.json(dados)
        with col2:
            st.markdown("**Representacao da placa:**")
            st.code(f"""
+----------------------------------+
| {dados.get('fabricante','WEG'):<32} |
| Motor Eletrico Industrial         |
+----------------------------------+
| Pot.:  {str(dados.get('potencia_kw','75')):<8} kW               |
| Tens.: {str(dados.get('tensao_v','380')):<8} V                |
| I.Nom:{str(dados.get('corrente_nom','100')):<9} A                |
| Prot.: {str(dados.get('ip_rating','IP55')):<26} |
+----------------------------------+
""", language="text")
