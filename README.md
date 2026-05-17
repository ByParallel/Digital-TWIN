# Digital Twin — Sprint 2: Visualização Operacional e Representação do Ativo

## Stack Tecnológico
- **Python 3.10+**
- **Streamlit** — Interface web operacional
- **SQLite** — Banco de dados local
- **Plotly** — Gráficos interativos
- **Pandas** — Manipulação de dados

## Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Iniciar a aplicação
python -m streamlit run app.py

# OU double-click em:
executar.bat
```

Acesse: **http://localhost:8501**

## Estrutura do Projeto

```
digital_twin/
├── app.py                    # Página inicial + inicialização do BD
├── database.py               # Camada de dados (SQLite)
├── requirements.txt
├── executar.bat              # Script de execução Windows
│
├── pages/
│   ├── 1_Navegacao.py        # Hierarquia Planta → Área → Ativo
│   ├── 2_Dashboard.py        # Sensores tempo real + histórico
│   ├── 3_Cadastro.py         # CRUD de ativos
│   ├── 4_RPA.py              # Central de automações RPA
│   └── 5_Pipeline.py         # Pipeline Placa → Cadastro
│
├── rpa/
│   ├── tag_association.py    # RPA: associação TAG/Localização
│   ├── record_updater.py     # RPA: atualização de registros
│   └── nameplate_pipeline.py # RPA: pipeline placa do motor
│
└── utils/
    ├── mock_data.py           # Gerador de dados simulados
    └── charts.py              # Componentes visuais (Plotly)
```

## Módulos da Sprint 2

| Módulo | Página | Descrição |
|--------|--------|-----------|
| Navegação | `1_Navegacao` | Hierarquia Planta → Área → Ativo com mapa |
| Dashboard | `2_Dashboard` | Gauges + gráficos temporais de 5 sensores |
| Cadastro | `3_Cadastro` | Registro, edição e exportação de ativos |
| RPA | `4_RPA` | Associação automática TAG/Localização + coleta |
| Pipeline | `5_Pipeline` | OCR Placa → Normalização → Banco de dados |

## Sensores Monitorados
- Tensão (V)
- Corrente (A)
- Temperatura (°C)
- Rotação (RPM)
- Vibração (mm/s)
- Potência (kW)
- Fator de Potência

## Estrutura do Banco de Dados

```
plantas ──< areas ──< ativos ──< leituras_sensores
                                log_rpa
```
