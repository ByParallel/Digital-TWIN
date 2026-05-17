"""
Sensor data simulator — Sprint 2
Uses the same SimuladorSensorIoT logic from Sprint 1 (Gaussian noise + anomaly injection).
"""
import random
import hashlib
import logging
from datetime import datetime, timedelta

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

log = logging.getLogger("sensor_simulator")


class SimuladorSensorIoT:
    """
    Replicates Sprint 1's SimuladorSensorIoT.
    Generates Gaussian-noise readings with configurable anomaly probability.
    In production: replace with paho-mqtt or OPC-UA client.
    """

    def __init__(self, ativo_id: int, codigo: str, ativo: dict, prob_anomalia: float = 0.04):
        self.ativo_id      = ativo_id
        self.codigo        = codigo
        self.prob_anomalia = prob_anomalia
        # Nominal values from nameplate (Sprint 1 field names)
        self._tensao_nom   = float(ativo.get("tensao_v",    380))
        self._corrente_nom = float(ativo.get("corrente_nom", 100))
        self._rpm_nom      = float(ativo.get("rpm",         1485))
        self._pot_nom      = float(ativo.get("potencia_kw",  75))

    def _gerar_base(self) -> dict:
        anomalia = random.random() < self.prob_anomalia
        if anomalia:
            return {
                "temperatura_c":  round(random.uniform(92, 105), 2),
                "vibracao_mm_s":  round(random.uniform(7.5, 12.0), 3),
                "corrente_a":     round(self._corrente_nom * random.uniform(1.35, 1.55), 2),
                "tensao_v":       round(self._tensao_nom * random.uniform(0.93, 0.97), 1),
                "rpm":            round(self._rpm_nom * random.uniform(0.93, 0.97), 0),
                "fator_potencia": round(random.uniform(0.72, 0.79), 3),
                "flag_anomalia":  1,
            }
        return {
            "temperatura_c":  round(random.gauss(65, 5), 2),
            "vibracao_mm_s":  round(random.gauss(2.5, 0.4), 3),
            "corrente_a":     round(random.gauss(self._corrente_nom * 0.88, self._corrente_nom * 0.06), 2),
            "tensao_v":       round(random.gauss(self._tensao_nom, 4), 1),
            "rpm":            round(random.gauss(self._rpm_nom, 8), 0),
            "fator_potencia": round(random.gauss(0.87, 0.02), 3),
            "flag_anomalia":  0,
        }

    def coletar(self, timestamp=None) -> dict:
        ts = (timestamp or datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
        leitura = self._gerar_base()
        leitura.update({"ativo_id": self.ativo_id, "fonte": "sensor_iot", "coletado_em": ts})
        conteudo = f"{self.ativo_id}{ts}{leitura['temperatura_c']}{leitura['corrente_a']}"
        leitura["hash_registro"] = hashlib.sha256(conteudo.encode()).hexdigest()[:32]
        return leitura

    def leitura_atual(self) -> dict:
        """Single live reading (not saved to DB)."""
        return self._gerar_base()


def _get_simuladores() -> dict:
    """Build one SimuladorSensorIoT per active asset."""
    ativos = db.get_ativos()
    return {
        a["codigo"]: SimuladorSensorIoT(a["id"], a["codigo"], a)
        for a in ativos
    }


def simular_leitura_atual(ativo: dict) -> dict:
    """Return one live reading dict (not persisted) for the given asset."""
    sim = SimuladorSensorIoT(ativo["id"], ativo["codigo"], ativo)
    return sim.leitura_atual()


def popular_historico(horas: int = 48, intervalo_min: int = 10) -> int:
    """Populate the DB with simulated history for all assets."""
    ativos = db.get_ativos()
    agora  = datetime.now()
    total  = 0

    for ativo in ativos:
        sim = SimuladorSensorIoT(ativo["id"], ativo["codigo"], ativo)
        ts  = agora - timedelta(hours=horas)
        while ts <= agora:
            leitura = sim.coletar(timestamp=ts)
            db.insert_leitura(ativo["id"], leitura)
            ts += timedelta(minutes=intervalo_min)
            total += 1

    return total


def executar_ciclo_coleta() -> list[dict]:
    """Batch: collect one reading per active asset and persist it."""
    ativos   = [a for a in db.get_ativos() if a.get("status") == "ativo"]
    resultados = []
    inicio   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    inseridas = 0

    for ativo in ativos:
        sim = SimuladorSensorIoT(ativo["id"], ativo["codigo"], ativo)
        leitura = sim.coletar()
        db.insert_leitura(ativo["id"], leitura)
        inseridas += 1
        resultados.append({
            "codigo": ativo["codigo"],
            "status": "Sucesso",
            "temperatura_c": leitura["temperatura_c"],
            "corrente_a":    leitura["corrente_a"],
            "flag_anomalia": leitura["flag_anomalia"],
        })

    db.registrar_execucao(
        "ciclo_coleta_sprint2", "sucesso",
        processados=inseridas, erros=0,
        detalhes={"ativos": len(ativos)},
        iniciado_em=inicio
    )
    return resultados
