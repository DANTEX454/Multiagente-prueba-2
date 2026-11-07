"""Los empleados de la oficina. Cada área = instrucciones propias + herramientas de cálculo."""
import json
import os
import anthropic
from calculos import HERRAMIENTAS

MODELO = os.getenv("MODELO", "claude-sonnet-5-5")


def _obtener_clave():
    """Busca la clave en variables de entorno y, si no, en los Secrets de Streamlit."""
    clave = os.getenv("ANTHROPIC_API_KEY")
    if clave:
        return clave
    try:
        import streamlit as st
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


CLAVE = _obtener_clave()
cliente = anthropic.Anthropic(api_key=CLAVE)

REGLAS = (
    "Responde en español, claro y profesional. Los cálculos los haces SIEMPRE con las herramientas "
    "disponibles; nunca inventes cifras. Si faltan datos, di exactamente cuáles. "
    "Estructura: 1) Hallazgos, 2) Interpretación, 3) Recomendaciones."
)

NUM_LISTA = {"type": "array", "items": {"type": "number"}}

AGENTES = {
    "contabilidad": {
        "nombre": "Contabilidad", "emoji": "📒",
        "system": "Eres el contador de la empresa. Revisas movimientos, clasificas cuentas (PUC colombiano cuando aplique), "
                  "verificas partida doble y detectas inconsistencias. " + REGLAS,
        "tools": [{
            "name": "verificar_partida_doble",
            "description": "Suma débitos y créditos y verifica que cuadren.",
            "input_schema": {"type": "object", "properties": {"debitos": NUM_LISTA, "creditos": NUM_LISTA},
                             "required": ["debitos", "creditos"]},
        }],
    },
    "proyectos": {
        "nombre": "Análisis de proyectos", "emoji": "📐",
        "system": "Eres analista de proyectos de inversión. Evalúas viabilidad con VPN, TIR y recuperación, "
                  "y señalas riesgos y supuestos débiles. Si no te dan la tasa de descuento, pídela o indica el supuesto. " + REGLAS,
        "tools": [{
            "name": "vpn_tir",
            "description": "Calcula VPN, TIR y payback. flujos[0] es la inversión inicial (negativa). tasa en decimal.",
            "input_schema": {"type": "object", "properties": {"flujos": NUM_LISTA, "tasa": {"type": "number"}},
                             "required": ["flujos", "tasa"]},
        }],
    },
    "diagnostico": {
        "nombre": "Diagnóstico empresarial", "emoji": "🩺",
        "system": "Eres consultor de diagnóstico empresarial. Analizas estados financieros con razones de liquidez, "
                  "endeudamiento y rentabilidad, y puedes complementar con DOFA. " + REGLAS,
        "tools": [{
            "name": "razones_financieras",
            "description": "Calcula razones financieras. Envía solo los datos que tengas.",
            "input_schema": {"type": "object", "properties": {k: {"type": "number"} for k in [
                "activo_corriente", "pasivo_corriente", "inventarios", "activo_total", "pasivo_total",
                "patrimonio", "ventas", "costo_ventas", "utilidad_neta"]}},
        }],
    },
    "proyecciones": {
        "nombre": "Proyección de demanda y ventas", "emoji": "📈",
        "system": "Eres analista de demanda y ventas. Extraes la serie de tiempo del documento, la proyectas con la herramienta "
                  "e interpretas tendencia, estacionalidad y confiabilidad del pronóstico. " + REGLAS,
        "tools": [{
            "name": "proyectar_serie",
            "description": "Proyecta una serie. estacionalidad=12 si es mensual, 4 si es trimestral, 0 si no hay.",
            "input_schema": {"type": "object", "properties": {
                "valores": NUM_LISTA, "periodos": {"type": "integer"}, "estacionalidad": {"type": "integer"}},
                "required": ["valores"]},
        }],
    },
}


def ejecutar_agente(area: str, documento: str, pregunta: str, avisar=lambda msg: None) -> str:
    cfg = AGENTES[area]
    mensajes = [{"role": "user", "content": f"Solicitud: {pregunta or 'Analiza este documento.'}\n\nDocumento:\n{documento}"}]

    for _ in range(6):  # máximo 6 vueltas de herramientas
        r = cliente.messages.create(model=MODELO, max_tokens=2500, system=cfg["system"],
                                    tools=cfg["tools"], messages=mensajes)
        if r.stop_reason != "tool_use":
            return "".join(b.text for b in r.content if b.type == "text")

        mensajes.append({"role": "assistant", "content": r.content})
        resultados = []
        for b in r.content:
            if b.type == "tool_use":
                avisar(f"{cfg['emoji']} {cfg['nombre']} está calculando con `{b.name}`…")
                try:
                    salida = HERRAMIENTAS[b.name](**b.input)
                except Exception as e:  # el agente verá el error y puede corregir
                    salida = {"error": str(e)}
                resultados.append({"type": "tool_result", "tool_use_id": b.id,
                                   "content": json.dumps(salida, ensure_ascii=False)})
        mensajes.append({"role": "user", "content": resultados})

    return "No logré completar el análisis. Intenta con una solicitud más específica."
