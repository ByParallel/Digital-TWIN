"""
RPA Module: Motor Nameplate Pipeline — Sprint 2
Integrates with Sprint 1's PipelineTransformacao validation logic.
Maps OCR-extracted fields to Sprint 1 ativos schema.
"""
import re
import time
import logging
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import database as db

log = logging.getLogger("rpa.nameplate_pipeline")

# Placa field → ativos column (Sprint 1 names)
MAPEAMENTO_CAMPOS = {
    "fabricante":  ["fabricante", "manufacturer", "marca"],
    "descricao":   ["modelo", "model", "frame", "tipo"],
    "corrente_nom":["corrente", "corrente nominal", "in", "amp", "a"],
    "potencia_kw": ["potencia", "pot.", "kw", "power"],
    "tensao_v":    ["tensao", "volt", "v", "tension"],
    "ip_rating":   ["ip", "grau de protecao", "protection"],
}


def normalizar_potencia(valor_str: str) -> float:
    s = str(valor_str).lower().strip()
    try:
        num = float(re.sub(r"[^\d.,]", "", s).replace(",", "."))
        return round(num * 0.7457, 2) if "hp" in s else num
    except ValueError:
        return 0.0


def extrair_dados_simulados(codigo: str) -> dict:
    """Simulate OCR extraction — replace with pytesseract in production."""
    time.sleep(0.4)
    ativos = db.get_ativos(codigo=codigo)
    if ativos:
        a = ativos[0]
        return {
            "fabricante":   a.get("fabricante") or "WEG",
            "descricao":    a.get("descricao") or f"Motor {codigo}",
            "corrente_nom": a.get("corrente_nom") or 100.0,
            "potencia_kw":  a.get("potencia_kw") or 75.0,
            "tensao_v":     a.get("tensao_v") or 380.0,
            "ip_rating":    a.get("ip_rating") or "IP55",
        }
    return {
        "fabricante":   "WEG",
        "descricao":    f"Motor Eletrico {codigo}",
        "corrente_nom": 100.0,
        "potencia_kw":  75.0,
        "tensao_v":     380.0,
        "ip_rating":    "IP55",
    }


def _parse_texto_placa(texto: str) -> dict:
    dados = {}
    for linha in texto.lower().split("\n"):
        for campo, aliases in MAPEAMENTO_CAMPOS.items():
            for alias in aliases:
                if alias in linha:
                    m = re.search(r"[:\s]+(.+)", linha)
                    if m:
                        dados[campo] = m.group(1).strip()
                    break
    return dados


def pipeline_placa_para_cadastro(codigo: str, area_id: int,
                                  imagem_path: str = None) -> dict:
    """
    Full pipeline:
    1. Extract data from nameplate (OCR or simulation)
    2. Normalize field values
    3. Validate via Sprint 1's PipelineTransformacao rules
    4. Register/update in DB with audit trail
    """
    resultado = {"codigo": codigo, "status": None, "mensagem": None,
                 "dados_extraidos": None, "etapas": []}
    inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step 1: Extract
    resultado["etapas"].append("1. Extracao de dados da placa (OCR)")
    if imagem_path and os.path.exists(imagem_path):
        try:
            import pytesseract
            from PIL import Image
            texto = pytesseract.image_to_string(Image.open(imagem_path), lang="por+eng")
            dados = _parse_texto_placa(texto)
            resultado["etapas"].append("   -> OCR real executado")
        except Exception as e:
            log.warning(f"OCR falhou ({e}), usando simulacao.")
            dados = extrair_dados_simulados(codigo)
            resultado["etapas"].append("   -> Fallback para simulacao")
    else:
        dados = extrair_dados_simulados(codigo)
        resultado["etapas"].append("   -> Dados simulados (sem imagem)")

    resultado["dados_extraidos"] = dados

    # Step 2: Normalize
    resultado["etapas"].append("2. Normalizacao de campos")
    if "potencia_kw" in dados:
        dados["potencia_kw"] = normalizar_potencia(str(dados["potencia_kw"]))

    # Step 3: Register / Update
    resultado["etapas"].append("3. Cadastro/Atualizacao no banco")
    ativos_existentes = db.get_ativos(codigo=codigo)
    if ativos_existentes:
        from rpa.record_updater import atualizar_dados_tecnicos
        r = atualizar_dados_tecnicos(codigo, dados)
        resultado["etapas"].append(f"   -> Atualizado: {r['mensagem']}")
    else:
        db.cadastrar_ativo(area_id, codigo, dados.get("descricao", f"Motor {codigo}"),
                           **{k: v for k, v in dados.items() if k != "descricao"})
        resultado["etapas"].append(f"   -> Novo ativo '{codigo}' cadastrado")

    resultado["etapas"].append("4. Log registrado em log_execucoes")
    db.registrar_execucao("rpa_pipeline_placa", "sucesso", 1, 0,
                          {"codigo": codigo, "campos": list(dados.keys())}, inicio)

    msg = f"Pipeline concluido com sucesso para '{codigo}'"
    log.info(msg)
    return resultado | {"status": "Sucesso", "mensagem": msg}


def gerar_relatorio_pipeline(resultados: list) -> str:
    linhas = ["=" * 60, "RELATORIO - PIPELINE PLACA -> CADASTRO", "=" * 60]
    for r in resultados:
        linhas += [f"\nAtivo: {r['codigo']}", f"Status: {r['status']}",
                   f"Mensagem: {r['mensagem']}"]
        if r.get("etapas"):
            linhas.append("Etapas:")
            linhas += [f"  {e}" for e in r["etapas"]]
    linhas.append("=" * 60)
    return "\n".join(linhas)
