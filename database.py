"""
Database layer — Sprint 2
Extends the Sprint 1 motores.db schema with plantas, areas, and TAG/location
columns on ativos. All Sprint 1 field names are preserved exactly.
"""
import sqlite3
import os
import json
import hashlib
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "motores.db")


@contextmanager
def get_conn():
    """Context manager with rollback — identical to Sprint 1."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Sprint 2 schema extensions ────────────────────────────────────────────────

SCHEMA_SPRINT2 = """
-- Navigation hierarchy (new in Sprint 2)
CREATE TABLE IF NOT EXISTS plantas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    descricao TEXT,
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS areas (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    planta_id INTEGER NOT NULL REFERENCES plantas(id),
    nome      TEXT NOT NULL,
    descricao TEXT
);

-- Extend ativos with TAG and location (Sprint 2)
-- Uses ALTER TABLE ADD COLUMN (idempotent via try/except at runtime)
"""

SPRINT2_COLUMNS = [
    ("ativos", "tag",                  "TEXT"),
    ("ativos", "area_id",              "INTEGER"),
    ("ativos", "latitude",             "REAL"),
    ("ativos", "longitude",            "REAL"),
    ("ativos", "localizacao_descricao","TEXT"),
]


def init_db():
    """Initialize Sprint 2 extensions on top of the Sprint 1 database."""
    with get_conn() as conn:
        conn.executescript(SCHEMA_SPRINT2)

        # Add columns to ativos if they don't exist yet
        existing = {r[1] for r in conn.execute("PRAGMA table_info(ativos)").fetchall()}
        for table, col, dtype in SPRINT2_COLUMNS:
            if col not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}")

        # Seed hierarchy if empty
        if conn.execute("SELECT COUNT(*) FROM plantas").fetchone()[0] == 0:
            _seed_hierarchy(conn)

        # Auto-assign TAGs to existing Sprint 1 assets if not set
        _assign_default_tags(conn)


def _seed_hierarchy(conn):
    conn.executescript("""
        INSERT INTO plantas (nome, descricao) VALUES
            ('Planta São Paulo', 'Unidade principal de produção'),
            ('Planta Campinas',  'Unidade de processamento secundário');

        INSERT INTO areas (planta_id, nome, descricao) VALUES
            (1, 'Sala de Máquinas',  'Bloco A - Resfriamento e utilidades'),
            (1, 'Utilidades',        'Bloco B - Ar comprimido e vapor'),
            (1, 'Linha de Produção', 'Linha 3 - Esteiras transportadoras'),
            (2, 'Área de Bombas',    'Estações de bombeamento');
    """)


def _assign_default_tags(conn):
    """Give Sprint 1 assets a TAG and area assignment if they don't have one."""
    defaults = {
        "MTR-001": ("MTR-001", 1, "Bloco A - Sala de Máquinas", -23.5505, -46.6333),
        "MTR-002": ("MTR-002", 2, "Bloco B - Utilidades",       -23.5510, -46.6340),
        "MTR-003": ("MTR-003", 3, "Linha de Produção 3",         -23.5515, -46.6345),
    }
    for codigo, (tag, area_id, localizacao, lat, lon) in defaults.items():
        conn.execute(
            """UPDATE ativos SET tag=?, area_id=?, localizacao_descricao=?,
               latitude=?, longitude=? WHERE codigo=? AND tag IS NULL""",
            (tag, area_id, localizacao, lat, lon, codigo)
        )


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_plantas():
    with get_conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM plantas ORDER BY nome")]


def get_areas(planta_id=None):
    with get_conn() as conn:
        if planta_id:
            rows = conn.execute(
                "SELECT a.*, p.nome as planta_nome FROM areas a "
                "JOIN plantas p ON p.id=a.planta_id WHERE a.planta_id=? ORDER BY a.nome",
                (planta_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT a.*, p.nome as planta_nome FROM areas a "
                "JOIN plantas p ON p.id=a.planta_id ORDER BY p.nome, a.nome"
            ).fetchall()
        return [dict(r) for r in rows]


def get_ativos(area_id=None, codigo=None):
    with get_conn() as conn:
        base = """SELECT a.*, ar.nome as area_nome, p.nome as planta_nome
                  FROM ativos a
                  LEFT JOIN areas ar ON ar.id=a.area_id
                  LEFT JOIN plantas p ON p.id=ar.planta_id"""
        if codigo:
            rows = conn.execute(base + " WHERE a.codigo=?", (codigo,)).fetchall()
        elif area_id:
            rows = conn.execute(base + " WHERE a.area_id=? ORDER BY a.codigo", (area_id,)).fetchall()
        else:
            rows = conn.execute(base + " ORDER BY p.nome, ar.nome, a.codigo").fetchall()
        return [dict(r) for r in rows]


def get_leituras(ativo_id, limit=288):
    """Returns readings ordered oldest-first for chart rendering."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM leituras WHERE ativo_id=? ORDER BY coletado_em DESC LIMIT ?",
            (ativo_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def insert_leitura(ativo_id: int, leitura: dict):
    """Insert one reading using Sprint 1's schema + SHA-256 idempotency."""
    campos = ["ativo_id", "fonte", "temperatura_c", "vibracao_mm_s", "corrente_a",
              "tensao_v", "rpm", "fator_potencia", "coletado_em", "processado_em",
              "flag_anomalia", "hash_registro"]
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conteudo = f"{ativo_id}{agora}{leitura.get('temperatura_c',0)}{leitura.get('corrente_a',0)}"
    hash_reg = hashlib.sha256(conteudo.encode()).hexdigest()[:32]

    registro = {
        "ativo_id":       ativo_id,
        "fonte":          leitura.get("fonte", "sensor_iot"),
        "temperatura_c":  leitura.get("temperatura_c"),
        "vibracao_mm_s":  leitura.get("vibracao_mm_s"),
        "corrente_a":     leitura.get("corrente_a"),
        "tensao_v":       leitura.get("tensao_v"),
        "rpm":            leitura.get("rpm"),
        "fator_potencia": leitura.get("fator_potencia"),
        "coletado_em":    agora,
        "processado_em":  agora,
        "flag_anomalia":  leitura.get("flag_anomalia", 0),
        "hash_registro":  hash_reg,
    }
    placeholders = ", ".join(["?"] * len(campos))
    valores = [registro[c] for c in campos]

    with get_conn() as conn:
        conn.execute(
            f"INSERT OR IGNORE INTO leituras ({', '.join(campos)}) VALUES ({placeholders})",
            valores
        )


def update_ativo(codigo: str, **fields):
    fields["atualizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sets = ", ".join(f"{k}=?" for k in fields)
    valores = list(fields.values()) + [codigo]
    with get_conn() as conn:
        antes = dict(conn.execute("SELECT * FROM ativos WHERE codigo=?", (codigo,)).fetchone())
        conn.execute(f"UPDATE ativos SET {sets} WHERE codigo=?", valores)
        _registrar_historico_interno(conn, "ativos", "UPDATE",
                                     antes["id"], antes, fields)


def cadastrar_ativo(area_id: int, codigo: str, descricao: str, **kwargs):
    campos = ["area_id", "codigo", "descricao"] + list(kwargs.keys())
    valores = [area_id, codigo, descricao] + list(kwargs.values())
    placeholders = ", ".join(["?"] * len(valores))
    with get_conn() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO ativos ({', '.join(campos)}) VALUES ({placeholders})",
            valores
        )
        ativo_id = conn.execute("SELECT id FROM ativos WHERE codigo=?", (codigo,)).fetchone()[0]
        _registrar_historico_interno(conn, "ativos", "INSERT", ativo_id, None,
                                     {"codigo": codigo, "descricao": descricao})


def _registrar_historico_interno(conn, tabela, operacao, reg_id, antes, depois):
    conn.execute(
        """INSERT INTO historico_atualizacoes
           (tabela, operacao, registro_id, dados_antes, dados_depois)
           VALUES (?,?,?,?,?)""",
        (tabela, operacao, reg_id,
         json.dumps(antes, default=str) if antes else None,
         json.dumps(depois, default=str) if depois else None)
    )


def registrar_execucao(automacao: str, status: str, processados=0, erros=0,
                        detalhes=None, iniciado_em=None):
    """Reuses Sprint 1's log_execucoes table."""
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO log_execucoes
               (automacao, status, registros_proc, registros_erro, detalhes,
                iniciado_em, finalizado_em)
               VALUES (?,?,?,?,?,?,datetime('now','localtime'))""",
            (automacao, status, processados, erros,
             json.dumps(detalhes or {}, default=str),
             iniciado_em or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )


def get_log_execucoes(limit=80):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM log_execucoes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_historico_atualizacoes(limit=30):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM historico_atualizacoes ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]
