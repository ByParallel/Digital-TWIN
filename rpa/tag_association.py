"""
RPA Module: TAG Association — Sprint 2
Automates linking of physical asset (codigo) to TAG, area, and plant location.
Uses Sprint 1's log_execucoes table for audit trail.
"""
import re
import time
import logging
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

log = logging.getLogger("rpa.tag_association")


def validar_tag(tag: str) -> bool:
    """Validate TAG format: PREFIX-AREA-NNN (e.g. MTR-001, MOT-CP-001)."""
    return bool(re.match(r"^[A-Z]{2,5}-[A-Z0-9]{1,4}-?\d{2,3}$", tag))


def associar_tag_localidade(codigo: str, area_id: int, localizacao: str,
                            tag: str = None) -> dict:
    """
    RPA: Associate an asset (by codigo) to an area and location.
    Optionally assign/update its TAG.
    """
    resultado = {"codigo": codigo, "status": None, "mensagem": None,
                 "timestamp": datetime.now().isoformat()}
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log.info(f"Associacao: codigo={codigo} area={area_id} local={localizacao}")

    # Validate TAG if provided
    if tag and not validar_tag(tag):
        msg = f"TAG invalida: '{tag}'. Use formato PREFIX-NNN ou PREFIX-AREA-NNN"
        db.registrar_execucao("rpa_associar_tag", "erro", 0, 1,
                              {"codigo": codigo, "erro": msg}, inicio)
        return resultado | {"status": "Erro", "mensagem": msg}

    # Check asset exists
    ativos = db.get_ativos(codigo=codigo)
    if not ativos:
        msg = f"Ativo '{codigo}' nao encontrado."
        db.registrar_execucao("rpa_associar_tag", "erro", 0, 1,
                              {"codigo": codigo, "erro": msg}, inicio)
        return resultado | {"status": "Erro", "mensagem": msg}

    # Check area exists
    areas = db.get_areas()
    if area_id not in {a["id"] for a in areas}:
        msg = f"Area id={area_id} nao encontrada."
        return resultado | {"status": "Erro", "mensagem": msg}

    # Execute
    time.sleep(0.3)
    campos = dict(area_id=area_id, localizacao_descricao=localizacao)
    if tag:
        campos["tag"] = tag
    db.update_ativo(codigo, **campos)

    msg = f"'{codigo}' associado: area={area_id}, local={localizacao}" + (f", tag={tag}" if tag else "")
    log.info(msg)
    db.registrar_execucao("rpa_associar_tag", "sucesso", 1, 0,
                          {"codigo": codigo, "area_id": area_id, "localizacao": localizacao}, inicio)
    return resultado | {"status": "Sucesso", "mensagem": msg}


def sincronizar_todas_tags() -> list:
    """RPA Batch: Validate TAG/location consistency for all assets."""
    log.info("Sincronizacao em lote de TAGs...")
    ativos = db.get_ativos()
    resultados = []
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = 0

    for ativo in ativos:
        codigo = ativo["codigo"]
        tag    = ativo.get("tag") or ""
        local  = ativo.get("localizacao_descricao") or ativo.get("localizacao") or ""

        if not tag:
            msg = f"Ativo {codigo} sem TAG definida"
            log.warning(msg)
            resultados.append({"codigo": codigo, "status": "Aviso", "mensagem": msg})
        elif not validar_tag(tag):
            msg = f"TAG '{tag}' com formato invalido"
            log.warning(msg)
            resultados.append({"codigo": codigo, "status": "Aviso", "mensagem": msg})
        elif not local:
            msg = f"{codigo} sem localizacao definida"
            log.warning(msg)
            resultados.append({"codigo": codigo, "status": "Aviso", "mensagem": msg})
        else:
            msg = f"{codigo} | TAG={tag} | {local}"
            log.info(msg)
            resultados.append({"codigo": codigo, "status": "Sucesso", "mensagem": msg})
            ok += 1
        time.sleep(0.05)

    db.registrar_execucao("rpa_sync_tags", "sucesso", ok, len(ativos) - ok,
                          {"total": len(ativos), "validos": ok}, inicio)
    return resultados


def atualizar_coordenadas(codigo: str, latitude: float, longitude: float) -> dict:
    """RPA: Update GPS coordinates for an asset."""
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        return {"codigo": codigo, "status": "Erro",
                "mensagem": "Coordenadas geograficas invalidas."}

    if not db.get_ativos(codigo=codigo):
        return {"codigo": codigo, "status": "Erro",
                "mensagem": f"Ativo '{codigo}' nao encontrado."}

    time.sleep(0.2)
    db.update_ativo(codigo, latitude=latitude, longitude=longitude)
    msg = f"Coordenadas atualizadas: {latitude:.6f}, {longitude:.6f}"
    db.registrar_execucao("rpa_coordenadas", "sucesso", 1, 0,
                          {"codigo": codigo, "lat": latitude, "lon": longitude}, inicio)
    return {"codigo": codigo, "status": "Sucesso", "mensagem": msg}
