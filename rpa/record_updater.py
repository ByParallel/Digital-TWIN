"""
RPA Module: Record Updater — Sprint 2
Automates status updates and technical data changes.
Extends Sprint 1's RepositorioAtivos logic; writes to log_execucoes.
"""
import time
import logging
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db
from utils.mock_data import SimuladorSensorIoT

log = logging.getLogger("rpa.record_updater")

STATUS_VALIDOS = ["ativo", "manutencao", "inativo", "em_teste"]


def atualizar_status_ativo(codigo: str, novo_status: str) -> dict:
    """RPA: Change operational status of an asset."""
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if novo_status not in STATUS_VALIDOS:
        return {"codigo": codigo, "status": "Erro",
                "mensagem": f"Status invalido. Use: {', '.join(STATUS_VALIDOS)}"}

    ativos = db.get_ativos(codigo=codigo)
    if not ativos:
        return {"codigo": codigo, "status": "Erro",
                "mensagem": f"Ativo '{codigo}' nao encontrado."}

    status_anterior = ativos[0]["status"]
    time.sleep(0.2)
    db.update_ativo(codigo, status=novo_status)
    msg = f"Status: {status_anterior} -> {novo_status}"
    log.info(f"{codigo} | {msg}")
    db.registrar_execucao("rpa_atualizar_status", "sucesso", 1, 0,
                          {"codigo": codigo, "de": status_anterior, "para": novo_status}, inicio)
    return {"codigo": codigo, "status": "Sucesso", "mensagem": msg}


def atualizar_dados_tecnicos(codigo: str, dados: dict) -> dict:
    """RPA: Update nameplate technical data for an asset."""
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Sprint 1 field names for ativos table
    campos_validos = {
        "descricao", "localizacao", "potencia_kw", "tensao_v",
        "corrente_nom", "ip_rating", "fabricante", "data_install", "tag"
    }
    dados_ok = {k: v for k, v in dados.items() if k in campos_validos and v is not None}

    if not dados_ok:
        return {"codigo": codigo, "status": "Aviso",
                "mensagem": "Nenhum campo valido para atualizar."}

    ativos = db.get_ativos(codigo=codigo)
    if not ativos:
        return {"codigo": codigo, "status": "Erro",
                "mensagem": f"Ativo '{codigo}' nao encontrado."}

    time.sleep(0.3)
    db.update_ativo(codigo, **dados_ok)
    msg = f"Campos atualizados: {list(dados_ok.keys())}"
    log.info(f"{codigo} | {msg}")
    db.registrar_execucao("rpa_dados_tecnicos", "sucesso", 1, 0,
                          {"codigo": codigo, "campos": list(dados_ok.keys())}, inicio)
    return {"codigo": codigo, "status": "Sucesso", "mensagem": msg,
            "campos_atualizados": list(dados_ok.keys())}


def coletar_e_salvar_leitura(codigo: str) -> dict:
    """RPA: Collect one sensor reading and persist it for a given asset."""
    ativos = db.get_ativos(codigo=codigo)
    if not ativos:
        return {"codigo": codigo, "status": "Erro",
                "mensagem": f"Ativo '{codigo}' nao encontrado."}

    ativo = ativos[0]
    sim   = SimuladorSensorIoT(ativo["id"], codigo, ativo)
    leitura = sim.coletar()
    db.insert_leitura(ativo["id"], leitura)

    msg = (f"T={leitura['temperatura_c']}C | I={leitura['corrente_a']}A | "
           f"V={leitura['vibracao_mm_s']}mm/s | "
           f"{'ANOMALIA' if leitura['flag_anomalia'] else 'normal'}")
    return {"codigo": codigo, "status": "Sucesso", "mensagem": msg, "leitura": leitura}
