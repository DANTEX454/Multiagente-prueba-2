"""Herramientas de cálculo. Las hace Python, no la IA, para que los números sean confiables."""
import numpy as np


# ---------- Proyectos ----------
def vpn_tir(flujos: list, tasa: float) -> dict:
    """flujos[0] es la inversión inicial (negativa). tasa en decimal (0.12 = 12 %)."""
    f = np.array(flujos, dtype=float)
    vpn = float(sum(v / (1 + tasa) ** t for t, v in enumerate(f)))

    def van(r):
        return sum(v / (1 + r) ** t for t, v in enumerate(f))

    tir = None
    lo, hi = -0.99, 10.0
    if van(lo) * van(hi) < 0:
        for _ in range(200):
            mid = (lo + hi) / 2
            if van(lo) * van(mid) <= 0:
                hi = mid
            else:
                lo = mid
        tir = (lo + hi) / 2

    acum, payback = 0.0, None
    for t, v in enumerate(f):
        previo = acum
        acum += v
        if acum >= 0 and payback is None and t > 0:
            payback = t - 1 + (-previo / v if v else 0)

    return {
        "vpn": round(vpn, 2),
        "tir": None if tir is None else round(tir, 4),
        "payback_periodos": None if payback is None else round(payback, 2),
        "decision": "Viable (VPN > 0)" if vpn > 0 else "No viable con esa tasa (VPN <= 0)",
    }


# ---------- Contabilidad ----------
def verificar_partida_doble(debitos: list, creditos: list) -> dict:
    d, c = float(sum(debitos)), float(sum(creditos))
    return {"total_debitos": d, "total_creditos": c,
            "diferencia": round(d - c, 2), "cuadra": abs(d - c) < 0.01}


# ---------- Diagnóstico ----------
def razones_financieras(activo_corriente=None, pasivo_corriente=None, inventarios=None,
                        activo_total=None, pasivo_total=None, patrimonio=None,
                        ventas=None, costo_ventas=None, utilidad_neta=None) -> dict:
    def div(a, b):
        return None if a is None or not b else round(a / b, 4)

    r = {
        "razon_corriente": div(activo_corriente, pasivo_corriente),
        "prueba_acida": div(None if activo_corriente is None else activo_corriente - (inventarios or 0), pasivo_corriente),
        "endeudamiento": div(pasivo_total, activo_total),
        "apalancamiento": div(pasivo_total, patrimonio),
        "margen_bruto": div(None if ventas is None or costo_ventas is None else ventas - costo_ventas, ventas),
        "margen_neto": div(utilidad_neta, ventas),
        "ROA": div(utilidad_neta, activo_total),
        "ROE": div(utilidad_neta, patrimonio),
        "rotacion_activos": div(ventas, activo_total),
    }
    return {k: v for k, v in r.items() if v is not None}


# ---------- Proyecciones ----------
def proyectar_serie(valores: list, periodos: int = 6, estacionalidad: int = 0) -> dict:
    """Holt (nivel + tendencia) con estacionalidad multiplicativa opcional.
    estacionalidad: 12 si son datos mensuales, 4 trimestrales, 0 si no hay."""
    y = np.array(valores, dtype=float)
    n = len(y)
    if n < 6:
        return {"error": "Se necesitan al menos 6 datos para proyectar."}

    s = int(estacionalidad)
    if s > 1 and n >= 2 * s:
        # índices estacionales sobre la serie sin tendencia (evita que la tendencia los distorsione)
        base = np.polyval(np.polyfit(np.arange(n), y, 1), np.arange(n))
        razon = y / base
        idx = np.array([razon[i::s].mean() for i in range(s)])
        idx = idx / idx.mean()
        des = y / np.array([idx[i % s] for i in range(n)])
    else:
        s, idx, des = 0, np.ones(1), y

    def ajustar(a, b):
        nivel, tend = des[0], des[1] - des[0]
        err = []
        for t in range(1, n):
            pred = nivel + tend
            err.append(abs(des[t] - pred))
            nuevo = a * des[t] + (1 - a) * (nivel + tend)
            tend = b * (nuevo - nivel) + (1 - b) * tend
            nivel = nuevo
        return np.mean(err), nivel, tend

    mejor = min(((ajustar(a, b), a, b) for a in np.arange(0.1, 1, 0.1) for b in np.arange(0.1, 1, 0.1)),
                key=lambda x: x[0][0])
    (mae, nivel, tend), a, b = mejor

    pron = []
    for h in range(1, int(periodos) + 1):
        base = nivel + h * tend
        pron.append(round(float(base * (idx[(n + h - 1) % s] if s else 1)), 2))

    return {
        "pronostico": pron,
        "error_medio_abs_(MAE)": round(float(mae), 2),
        "error_relativo_%": round(float(mae / np.mean(des) * 100), 2),
        "tendencia_por_periodo": round(float(tend), 2),
        "alpha_beta": [round(float(a), 1), round(float(b), 1)],
        "estacionalidad_usada": s,
    }


HERRAMIENTAS = {
    "vpn_tir": vpn_tir,
    "verificar_partida_doble": verificar_partida_doble,
    "razones_financieras": razones_financieras,
    "proyectar_serie": proyectar_serie,
}
