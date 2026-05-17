import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# Sprint 1 field names
CORES = {
    "tensao_v":       "#4CAF50",
    "corrente_a":     "#2196F3",
    "temperatura_c":  "#FF5722",
    "rpm":            "#9C27B0",
    "vibracao_mm_s":  "#FF9800",
    "fator_potencia": "#607D8B",
}

LABELS = {
    "tensao_v":       "Tensão (V)",
    "corrente_a":     "Corrente (A)",
    "temperatura_c":  "Temperatura (°C)",
    "rpm":            "Rotação (RPM)",
    "vibracao_mm_s":  "Vibração (mm/s)",
    "fator_potencia": "Fator de Potência",
}

LIMITES_ALERTA = {
    "temperatura_c": 85,
    "vibracao_mm_s": 6.0,
}


def gauge_card(valor, label, min_val, max_val, alerta=None, cor="#2196F3"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={"text": label, "font": {"size": 14}},
        number={"font": {"size": 22}},
        gauge={
            "axis": {"range": [min_val, max_val]},
            "bar": {"color": cor},
            "steps": [
                {"range": [min_val, max_val * 0.6],  "color": "#e8f5e9"},
                {"range": [max_val * 0.6, max_val * 0.85], "color": "#fff3e0"},
                {"range": [max_val * 0.85, max_val], "color": "#ffebee"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 3},
                "thickness": 0.75,
                "value": alerta,
            } if alerta else {},
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
    return fig


def grafico_historico(df: pd.DataFrame, coluna: str):
    cor   = CORES.get(coluna, "#2196F3")
    label = LABELS.get(coluna, coluna)
    alerta = LIMITES_ALERTA.get(coluna)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["coletado_em"], y=df[coluna],
        mode="lines", name=label,
        line=dict(color=cor, width=2),
    ))
    if alerta:
        fig.add_hline(y=alerta, line_dash="dash", line_color="red",
                      annotation_text=f"Limite: {alerta}",
                      annotation_position="top right")

    fig.update_layout(
        title=label, xaxis_title="Horário", yaxis_title=label,
        height=300, margin=dict(l=40, r=20, t=40, b=40),
        template="plotly_white", hovermode="x unified",
    )
    return fig


def grafico_multi_sensor(df: pd.DataFrame, colunas: list):
    fig = make_subplots(
        rows=len(colunas), cols=1, shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[LABELS.get(c, c) for c in colunas],
    )
    for i, col in enumerate(colunas, 1):
        fig.add_trace(
            go.Scatter(x=df["coletado_em"], y=df[col],
                       name=LABELS.get(col, col),
                       line=dict(color=CORES.get(col, "#666"), width=1.5)),
            row=i, col=1
        )
        alerta = LIMITES_ALERTA.get(col)
        if alerta:
            fig.add_hline(y=alerta, line_dash="dash", line_color="red", row=i, col=1)

    fig.update_layout(
        height=150 * len(colunas) + 80,
        template="plotly_white", showlegend=False,
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def grafico_status_ativos(ativos: list):
    status_count = {}
    for a in ativos:
        s = a.get("status", "desconhecido")
        status_count[s] = status_count.get(s, 0) + 1

    cores = {"ativo": "#4CAF50", "manutencao": "#FF9800", "inativo": "#F44336"}
    fig = go.Figure(go.Pie(
        labels=list(status_count.keys()),
        values=list(status_count.values()),
        marker_colors=[cores.get(k, "#9E9E9E") for k in status_count],
        hole=0.4,
    ))
    fig.update_layout(title="Status dos Ativos", height=280,
                      margin=dict(l=10, r=10, t=40, b=10))
    return fig


def grafico_anomalias(df: pd.DataFrame):
    anomalias = df[df["flag_anomalia"] == 1]
    normais   = df[df["flag_anomalia"] == 0]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=normais["coletado_em"], y=normais["temperatura_c"],
        mode="lines", name="Normal", line=dict(color="#4CAF50", width=1.5)
    ))
    fig.add_trace(go.Scatter(
        x=anomalias["coletado_em"], y=anomalias["temperatura_c"],
        mode="markers", name="Anomalia",
        marker=dict(color="red", size=8, symbol="x")
    ))
    fig.update_layout(
        title="Temperatura com deteccao de anomalias",
        xaxis_title="Horario", yaxis_title="Temperatura (C)",
        height=320, template="plotly_white", hovermode="x unified",
    )
    return fig
