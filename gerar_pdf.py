from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime

OUTPUT = "Documento_Tecnico_Sprint2.pdf"

doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4,
    rightMargin=2*cm, leftMargin=2*cm,
    topMargin=2.5*cm, bottomMargin=2*cm
)

styles = getSampleStyleSheet()

# Custom styles
titulo = ParagraphStyle("titulo", parent=styles["Title"],
    fontSize=22, textColor=colors.HexColor("#1a237e"),
    spaceAfter=6, alignment=TA_CENTER)

subtitulo = ParagraphStyle("subtitulo", parent=styles["Normal"],
    fontSize=12, textColor=colors.HexColor("#3949ab"),
    spaceAfter=4, alignment=TA_CENTER)

h1 = ParagraphStyle("h1", parent=styles["Heading1"],
    fontSize=14, textColor=colors.HexColor("#1a237e"),
    spaceBefore=16, spaceAfter=6,
    borderPad=4)

h2 = ParagraphStyle("h2", parent=styles["Heading2"],
    fontSize=12, textColor=colors.HexColor("#283593"),
    spaceBefore=10, spaceAfter=4)

corpo = ParagraphStyle("corpo", parent=styles["Normal"],
    fontSize=10, leading=16, alignment=TA_JUSTIFY,
    spaceAfter=6)

codigo = ParagraphStyle("codigo", parent=styles["Code"],
    fontSize=8, leading=12, backColor=colors.HexColor("#f5f5f5"),
    leftIndent=12, rightIndent=12, spaceBefore=4, spaceAfter=4,
    fontName="Courier")

def tabela(dados, col_widths=None, header=True):
    t = Table(dados, colWidths=col_widths)
    estilo = [
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#3949ab")),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#f8f9ff"), colors.white]),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#c5cae9")),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("PADDING",    (0,0), (-1,-1), 5),
    ]
    if not header:
        estilo[0] = ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8eaf6"))
        estilo[1] = ("TEXTCOLOR",  (0,0), (-1,0), colors.black)
    t.setStyle(TableStyle(estilo))
    return t

def hr():
    return HRFlowable(width="100%", thickness=1,
                      color=colors.HexColor("#c5cae9"), spaceAfter=8)

# ── Content ────────────────────────────────────────────────────────────────────
story = []

# CAPA
story += [
    Spacer(1, 2*cm),
    Paragraph("DOCUMENTO TECNICO", titulo),
    Paragraph("Sprint 2 — Visualizacao Operacional e Representacao do Ativo", subtitulo),
    Spacer(1, 0.4*cm),
    Paragraph("Monitoramento Preditivo de Motores Eletricos Industriais", subtitulo),
    Spacer(1, 1*cm),
    hr(),
    Spacer(1, 0.4*cm),
    Paragraph(f"Data: {datetime.now().strftime('%d/%m/%Y')}", ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10)),
    Paragraph("Projeto: Digital Twin Industrial", ParagraphStyle("c", parent=styles["Normal"], alignment=TA_CENTER, fontSize=10)),
    Spacer(1, 1.2*cm),
    tabela([
        ["Integrante", "RM"],
        ["Arthur Baptista dos Santos", "565346"],
        ["Joao Pedro",                 "561738"],
        ["Nelson Felix",               "565603"],
    ], col_widths=[9*cm, 6.5*cm]),
    Spacer(1, 1*cm),
]

# SUMÁRIO
story.append(Paragraph("SUMARIO", h1))
story.append(hr())
sumario = [
    ["1.", "Visao Geral do Projeto"],
    ["2.", "Continuidade com a Sprint 1"],
    ["3.", "Arquitetura da Solucao"],
    ["4.", "Mapeamento Ativo-TAG-Localizacao"],
    ["5.", "Pipeline Placa -> Cadastro"],
    ["6.", "Modulos RPA"],
    ["7.", "Interface e Visualizacao"],
    ["8.", "Requisitos Atendidos"],
    ["9.", "Tecnologias Utilizadas"],
    ["10.", "Estrutura de Arquivos"],
]
story.append(tabela(
    [["#", "Secao"]] + sumario,
    col_widths=[1.5*cm, 14*cm]
))
story.append(PageBreak())

# 1. VISAO GERAL
story.append(Paragraph("1. Visao Geral do Projeto", h1))
story.append(hr())
story.append(Paragraph(
    "O projeto consiste em um <b>Digital Twin de Motores Eletricos Industriais</b> — "
    "uma representacao digital de ativos fisicos de uma planta industrial. "
    "O sistema permite monitorar, localizar e analisar cada motor remotamente, "
    "sem necessidade de deslocamento fisico ate o equipamento.", corpo))
story.append(Paragraph(
    "A Sprint 2 evolui a base de dados e automacao construida na Sprint 1, "
    "adicionando navegacao hierarquica pela planta, dashboards operacionais "
    "com sensores em tempo real, automacoes RPA e um pipeline de integracao "
    "de dados da placa do motor.", corpo))
story.append(Spacer(1, 0.3*cm))

# 2. CONTINUIDADE
story.append(Paragraph("2. Continuidade com a Sprint 1", h1))
story.append(hr())
story.append(Paragraph(
    "A Sprint 2 herda diretamente o banco <b>motores.db</b> gerado na Sprint 1, "
    "preservando todos os dados e ampliando o schema sem quebrar compatibilidade.", corpo))
story.append(Spacer(1, 0.2*cm))
story.append(tabela([
    ["Componente Sprint 1", "Uso na Sprint 2"],
    ["motores.db (SQLite)", "Banco base — extendido com tabelas plantas e areas"],
    ["Tabela ativos", "Recebe colunas tag, area_id, latitude, longitude"],
    ["Tabela leituras", "Usada diretamente pelo dashboard e RPA de coleta"],
    ["log_execucoes", "Recebe logs de todas as operacoes RPA da Sprint 2"],
    ["historico_atualizacoes", "Registra antes/depois de cada UPDATE em ativos"],
    ["SimuladorSensorIoT", "Reutilizado com ruido gaussiano e anomalia probabilistica"],
    ["Hash SHA-256", "Mantido para idempotencia nas insercoes de leituras"],
    ["3 ativos (MTR-001/002/003)", "Ativos reais exibidos na interface"],
], col_widths=[7*cm, 8.5*cm]))
story.append(PageBreak())

# 3. ARQUITETURA
story.append(Paragraph("3. Arquitetura da Solucao", h1))
story.append(hr())
story.append(Paragraph(
    "A solucao e estruturada em tres camadas principais:", corpo))

story.append(tabela([
    ["Camada", "Componente", "Responsabilidade"],
    ["Interface", "Streamlit (5 paginas)", "Navegacao, dashboards, cadastro"],
    ["Automacao", "Modulos RPA (3 scripts)", "Associacao TAG, coleta, pipeline placa"],
    ["Dados", "SQLite + database.py", "Persistencia, auditoria, historico"],
], col_widths=[3*cm, 6*cm, 6.5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("Diagrama de Fluxo:", h2))
story.append(Paragraph(
    "[Interface Streamlit] --> [Modulos RPA] --> [database.py] --> [motores.db]", codigo))
story.append(Paragraph(
    "                                   |                              |", codigo))
story.append(Paragraph(
    "                         [log_execucoes]          [historico_atualizacoes]", codigo))
story.append(Spacer(1, 0.5*cm))

# 4. MAPEAMENTO
story.append(Paragraph("4. Mapeamento Ativo-TAG-Localizacao", h1))
story.append(hr())
story.append(Paragraph(
    "Cada ativo fisico e rastreavel pela sua TAG, area de instalacao e localizacao geografica. "
    "A hierarquia de navegacao e: <b>Planta -> Area -> Ativo</b>.", corpo))
story.append(Spacer(1, 0.2*cm))

story.append(Paragraph("4.1 Hierarquia de Plantas e Areas", h2))
story.append(tabela([
    ["Planta", "Area", "Descricao"],
    ["Planta Sao Paulo", "Sala de Maquinas", "Bloco A - Resfriamento"],
    ["Planta Sao Paulo", "Utilidades", "Bloco B - Ar comprimido"],
    ["Planta Sao Paulo", "Linha de Producao", "Linha 3 - Esteiras"],
    ["Planta Campinas", "Area de Bombas", "Estacoes de bombeamento"],
], col_widths=[5*cm, 5*cm, 5.5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("4.2 Ativos Cadastrados (Sprint 1)", h2))
story.append(tabela([
    ["Codigo", "TAG", "Descricao", "kW", "Tensao", "IP", "Status"],
    ["MTR-001", "MTR-001", "Motor Bomba Resfriamento", "75", "380V", "IP55", "ativo"],
    ["MTR-002", "MTR-002", "Motor Compressor Ar", "45", "380V", "IP54", "ativo"],
    ["MTR-003", "MTR-003", "Motor Esteira Linha 3", "22", "220V", "IP65", "ativo"],
], col_widths=[2.2*cm, 2.2*cm, 5*cm, 1.5*cm, 2*cm, 1.5*cm, 1.5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("4.3 Campos de Rastreabilidade em ativos", h2))
story.append(tabela([
    ["Campo", "Tipo", "Descricao"],
    ["codigo", "TEXT UNIQUE", "Identificador do ativo fisico"],
    ["tag", "TEXT", "TAG operacional (adicionada Sprint 2)"],
    ["area_id", "INTEGER FK", "Vinculo com a area da planta"],
    ["localizacao", "TEXT", "Descricao textual do local fisico"],
    ["localizacao_descricao", "TEXT", "Descricao detalhada (Sprint 2)"],
    ["latitude / longitude", "REAL", "Coordenadas GPS do equipamento"],
    ["atualizado_em", "TEXT", "Timestamp do ultimo UPDATE"],
], col_widths=[4*cm, 3.5*cm, 8*cm]))
story.append(PageBreak())

# 5. PIPELINE PLACA
story.append(Paragraph("5. Pipeline Placa -> Cadastro", h1))
story.append(hr())
story.append(Paragraph(
    "Define o fluxo completo desde a captura da imagem da placa do motor "
    "ate o preenchimento automatico do cadastro digital.", corpo))
story.append(Spacer(1, 0.2*cm))

story.append(tabela([
    ["Etapa", "Componente", "Entrada", "Saida"],
    ["1. Captura", "Camera/Upload", "Foto da placa fisica", "Imagem JPG/PNG"],
    ["2. OCR", "pytesseract", "Imagem da placa", "Texto bruto extraido"],
    ["3. Parse", "_parse_texto_placa()", "Texto bruto", "Dict de campos"],
    ["4. Normalizacao", "normalizar_potencia()", "HP ou kW (string)", "Float kW"],
    ["5. Cadastro", "database.update_ativo()", "Dict normalizado", "Registro atualizado"],
    ["6. Auditoria", "historico_atualizacoes", "Estado antes/depois", "JSON no banco"],
], col_widths=[2.5*cm, 4*cm, 4*cm, 5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("5.1 Mapeamento Campo da Placa -> Banco de Dados", h2))
story.append(tabela([
    ["Campo na Placa Fisica", "Alias Reconhecidos", "Coluna em ativos (Sprint 1)"],
    ["Fabricante", "fabricante, manufacturer, marca", "fabricante"],
    ["Modelo/Frame", "modelo, model, frame", "descricao"],
    ["Corrente Nominal", "corrente, in, amp, a", "corrente_nom"],
    ["Potencia", "potencia, kw, hp, power", "potencia_kw"],
    ["Tensao", "tensao, volt, v, tension", "tensao_v"],
    ["Protecao IP", "ip, grau de protecao", "ip_rating"],
], col_widths=[4*cm, 6.5*cm, 5*cm]))
story.append(PageBreak())

# 6. MODULOS RPA
story.append(Paragraph("6. Modulos RPA", h1))
story.append(hr())
story.append(Paragraph(
    "Tres modulos automatizam operacoes sem necessidade de input manual repetitivo. "
    "Todas as operacoes registram entrada em <b>log_execucoes</b> (Sprint 1).", corpo))
story.append(Spacer(1, 0.2*cm))

story.append(tabela([
    ["Modulo", "Arquivo", "Operacoes"],
    ["Associacao TAG", "rpa/tag_association.py",
     "associar_tag_localidade(), sincronizar_todas_tags(), atualizar_coordenadas()"],
    ["Atualizacao de Registros", "rpa/record_updater.py",
     "atualizar_status_ativo(), atualizar_dados_tecnicos(), coletar_e_salvar_leitura()"],
    ["Pipeline Placa", "rpa/nameplate_pipeline.py",
     "pipeline_placa_para_cadastro(), extrair_dados_simulados(), gerar_relatorio_pipeline()"],
], col_widths=[3.5*cm, 5*cm, 7*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("6.1 Fluxo da Automacao de Associacao TAG", h2))
story.append(tabela([
    ["Passo", "Acao", "Resultado em caso de falha"],
    ["1", "Validar formato da TAG (regex)", "Retorna status='Erro'"],
    ["2", "Verificar existencia do ativo no banco", "Retorna status='Erro'"],
    ["3", "Verificar existencia da area", "Retorna status='Erro'"],
    ["4", "Executar UPDATE em ativos", "Rollback automatico (WAL)"],
    ["5", "Registrar em log_execucoes", "Sempre executado"],
], col_widths=[1.5*cm, 7*cm, 7*cm]))
story.append(PageBreak())

# 7. INTERFACE
story.append(Paragraph("7. Interface e Visualizacao", h1))
story.append(hr())
story.append(tabela([
    ["Pagina", "Funcionalidade Principal"],
    ["app.py (Home)", "KPIs gerais, tabela de ativos, filtros por planta e status"],
    ["1_Navegacao", "Hierarquia Planta > Area > Ativo, ficha tecnica, mapa GPS"],
    ["2_Dashboard", "Metricas ao vivo, 4 gauges, graficos historicos, deteccao de anomalias"],
    ["3_Cadastro", "CRUD completo de ativos, exportacao CSV"],
    ["4_RPA", "Central de automacoes, log de execucoes, historico de auditoria"],
    ["5_Pipeline", "Execucao do pipeline, mapeamento TAG/local, simulacao OCR"],
], col_widths=[4*cm, 11.5*cm]))
story.append(Spacer(1, 0.4*cm))

story.append(Paragraph("7.1 Sensores Monitorados no Dashboard", h2))
story.append(tabela([
    ["Sensor", "Campo no Banco", "Limite de Alerta", "Visualizacao"],
    ["Temperatura", "temperatura_c", "> 85 degC", "Gauge + grafico temporal"],
    ["Corrente", "corrente_a", "> 125% I.nom", "Gauge + grafico temporal"],
    ["Vibracao", "vibracao_mm_s", "> 6.0 mm/s", "Gauge + grafico temporal"],
    ["Rotacao", "rpm", "—", "Metrica + grafico temporal"],
    ["Tensao", "tensao_v", "—", "Metrica + grafico temporal"],
    ["Fator de Potencia", "fator_potencia", "—", "Gauge"],
], col_widths=[3*cm, 3.5*cm, 3.5*cm, 5.5*cm]))
story.append(PageBreak())

# 8. REQUISITOS
story.append(Paragraph("8. Requisitos Atendidos", h1))
story.append(hr())
story.append(tabela([
    ["Requisito", "Descricao", "Atendimento"],
    ["RF1", "Atualizacao de registros sem input manual repetitivo", "Modulos RPA + log_execucoes"],
    ["RF2", "Localizar equipamento pela TAG", "Pagina Navegacao + selectbox por codigo/TAG"],
    ["RF3", "Exibir metricas de sensores em dashboards dinamicos", "Dashboard com gauges e graficos Plotly"],
    ["RF4", "Pipeline placa -> cadastro definido", "rpa/nameplate_pipeline.py completo"],
    ["RNF1", "Codigo versionado em GitHub", "Estrutura modular pronta para git"],
    ["RNF2", "Interface amigavel para tecnico de manutencao", "Streamlit com navegacao simples"],
    ["RNF3", "Rastreabilidade e controle de acesso", "historico_atualizacoes + log_execucoes"],
    ["RNF4", "Preparado para Machine Learning", "flag_anomalia + series temporais estruturadas"],
], col_widths=[1.5*cm, 8*cm, 6*cm]))
story.append(PageBreak())

# 9. TECNOLOGIAS
story.append(Paragraph("9. Tecnologias Utilizadas", h1))
story.append(hr())
story.append(tabela([
    ["Tecnologia", "Versao", "Papel"],
    ["Python", "3.12", "Linguagem base"],
    ["Streamlit", "1.28.2", "Interface web operacional"],
    ["SQLite", "3.x (stdlib)", "Banco de dados (herdado Sprint 1)"],
    ["Plotly", "5.x", "Graficos interativos e gauges"],
    ["Pandas", "2.x", "Manipulacao de dados e tabelas"],
    ["Pillow", "10.x", "Processamento de imagens (pipeline OCR)"],
    ["pytesseract", "0.3.x", "OCR da placa do motor (producao)"],
    ["hashlib (stdlib)", "—", "SHA-256 para idempotencia (Sprint 1)"],
    ["logging (stdlib)", "—", "Rastreabilidade de execucoes (Sprint 1)"],
], col_widths=[4*cm, 3*cm, 8.5*cm]))
story.append(Spacer(1, 0.5*cm))

# 10. ESTRUTURA
story.append(Paragraph("10. Estrutura de Arquivos", h1))
story.append(hr())
story.append(Paragraph(
    "digital_twin/", codigo))
story.append(Paragraph(
    "  app.py                    # Pagina inicial + inicializacao", codigo))
story.append(Paragraph(
    "  database.py               # Camada de dados (estende motores.db)", codigo))
story.append(Paragraph(
    "  requirements.txt", codigo))
story.append(Paragraph(
    "  data/motores.db           # Banco SQLite (herdado Sprint 1)", codigo))
story.append(Paragraph(
    "  pages/", codigo))
story.append(Paragraph(
    "    1_Navegacao.py          # Hierarquia Planta > Area > Ativo", codigo))
story.append(Paragraph(
    "    2_Dashboard.py          # Sensores tempo real + historico", codigo))
story.append(Paragraph(
    "    3_Cadastro.py           # CRUD de ativos", codigo))
story.append(Paragraph(
    "    4_RPA.py                # Central de automacoes", codigo))
story.append(Paragraph(
    "    5_Pipeline.py           # Pipeline placa -> cadastro", codigo))
story.append(Paragraph(
    "  rpa/", codigo))
story.append(Paragraph(
    "    tag_association.py      # RPA: associacao TAG/Localizacao", codigo))
story.append(Paragraph(
    "    record_updater.py       # RPA: atualizacao de registros", codigo))
story.append(Paragraph(
    "    nameplate_pipeline.py   # RPA: pipeline da placa do motor", codigo))
story.append(Paragraph(
    "  utils/", codigo))
story.append(Paragraph(
    "    mock_data.py            # SimuladorSensorIoT (Sprint 1)", codigo))
story.append(Paragraph(
    "    charts.py               # Graficos Plotly", codigo))

story.append(Spacer(1, 1*cm))
story.append(hr())
story.append(Paragraph(
    f"Documento gerado automaticamente em {datetime.now().strftime('%d/%m/%Y as %H:%M')} — Sprint 2 Digital Twin",
    ParagraphStyle("rodape", parent=styles["Normal"],
                   fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
))

doc.build(story)
print(f"PDF gerado: {OUTPUT}")
