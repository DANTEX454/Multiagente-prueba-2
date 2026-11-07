"""El gerente: lee el documento y decide a qué área lo envía."""
import json
from agentes import cliente, MODELO, AGENTES

SYSTEM = """Eres el gerente de una oficina virtual. Recibes un documento y una solicitud, y decides qué área lo atiende.
Áreas: contabilidad (movimientos, libros, asientos, conciliaciones), proyectos (flujos de inversión, VPN/TIR, viabilidad),
diagnostico (estados financieros, razones, DOFA, salud de la empresa), proyecciones (series de ventas/demanda en el tiempo).
Responde SOLO un JSON: {"area": "<una de las cuatro>", "razon": "<una frase>"}"""


def decidir_area(documento: str, pregunta: str) -> dict:
    r = cliente.messages.create(
        model=MODELO, max_tokens=200, system=SYSTEM,
        messages=[{"role": "user", "content": f"Solicitud: {pregunta}\n\nInicio del documento:\n{documento[:3000]}"}],
    )
    texto = "".join(b.text for b in r.content if b.type == "text").replace("```json", "").replace("```", "").strip()
    try:
        d = json.loads(texto)
        if d.get("area") in AGENTES:
            return d
    except json.JSONDecodeError:
        pass
    return {"area": "diagnostico", "razon": "No pude clasificarlo con certeza; lo envío a diagnóstico."}
