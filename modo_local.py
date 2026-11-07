"""Modo sin IA: el gerente clasifica con reglas y cada área calcula con Python. No necesita clave de API."""
import re
import pandas as pd
from calculos import vpn_tir, verificar_partida_doble, razones_financieras, proyectar_serie


def _n(s):
    return str(s).strip().lower()


def _fmt(x, dec=0):
    if x is None:
        return "—"
    s = f"{x:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _m(x):
    return ("-$" if x < 0 else "$") + _fmt(abs(x))


def _tabla(encabezados, filas):
    t = "| " + " | ".join(encabezados) + " |\n|" + "---|" * len(encabezados) + "\n"
    return t + "\n".join("| " + " | ".join(str(c) for c in f) + " |" for f in filas)


def _num(serie):
    return pd.to_numeric(serie, errors="coerce")


# ---------------------------------------------------------------- Gerente
def clasificar_local(tablas: dict, pregunta: str = "") -> dict:
    q = _n(pregunta)
    if re.search(r"proyecta|proyecci|pron[oó]stic|demanda", q):
        return {"area": "proyecciones", "razon": "Tu solicitud pide una proyección."}
    if re.search(r"viable|\bvpn\b|\btir\b|inversi", q):
        return {"area": "proyectos", "razon": "Tu solicitud trata de la viabilidad de un proyecto."}
    if re.search(r"cuadra|asiento|libro diario|partida doble", q):
        return {"area": "contabilidad", "razon": "Tu solicitud trata de verificar movimientos contables."}
    if re.search(r"diagn[oó]stic|razones|liquidez|endeud", q):
        return {"area": "diagnostico", "razon": "Tu solicitud pide un diagnóstico financiero."}

    cols = [_n(c) for df in tablas.values() for c in df.columns]
    filas = [_n(v) for df in tablas.values() if len(df.columns) for v in df.iloc[:, 0].tolist()]
    if any("debito" in c or "débito" in c for c in cols) and any("credito" in c or "crédito" in c for c in cols):
        return {"area": "contabilidad", "razon": "El archivo tiene columnas de débito y crédito."}
    if any(f in filas for f in ("total activo", "total pasivo", "total patrimonio")):
        return {"area": "diagnostico", "razon": "El archivo parece un balance o estado de resultados."}
    if any("flujo" in c for c in cols):
        return {"area": "proyectos", "razon": "El archivo tiene flujos de caja de un proyecto."}
    if any(len(df) >= 6 and _num(df.iloc[:, -1]).notna().sum() >= 6 for df in tablas.values() if len(df.columns) > 1):
        return {"area": "proyecciones", "razon": "El archivo parece una serie de datos en el tiempo."}
    return {"area": "diagnostico", "razon": "No pude clasificarlo con certeza; lo envío a diagnóstico."}


# ---------------------------------------------------------------- Contabilidad
def _contabilidad(tablas, pregunta):
    for nombre, df in tablas.items():
        cols = {_n(c): c for c in df.columns}
        cd = next((v for k, v in cols.items() if "debito" in k or "débito" in k), None)
        cc = next((v for k, v in cols.items() if "credito" in k or "crédito" in k), None)
        if cd and cc:
            break
    else:
        return "No encontré columnas de **débito** y **crédito**. Revisa que el archivo las tenga."

    d, c = _num(df[cd]).fillna(0), _num(df[cc]).fillna(0)
    total = verificar_partida_doble(d.tolist(), c.tolist())
    out = ["### Hallazgos", f"- Movimientos revisados: **{len(df)}**",
           f"- Total débitos: **{_m(total['total_debitos'])}**", f"- Total créditos: **{_m(total['total_creditos'])}**",
           f"- Diferencia: **{_m(total['diferencia'])}** → {'✅ el libro cuadra' if total['cuadra'] else '⚠️ el libro NO cuadra'}"]

    comp = next((v for k, v in cols.items() if k in ("comprobante", "asiento", "numero", "número")), None)
    if comp is not None:
        g = pd.DataFrame({"comp": df[comp], "d": d, "c": c}).groupby("comp", sort=False).sum()
        mal = g[(g["d"] - g["c"]).abs() > 0.01]
        out.append("\n### Comprobantes descuadrados")
        if mal.empty:
            out.append("Todos los comprobantes cuadran.")
        else:
            out.append(_tabla(["Comprobante", "Débitos", "Créditos", "Diferencia"],
                              [(i, _fmt(r.d), _fmt(r.c), _fmt(r.d - r.c)) for i, r in mal.iterrows()]))
    out.append("\n### Recomendaciones\n- Corrige los comprobantes descuadrados antes de cerrar el período.\n"
               "- Verifica que cada asiento tenga el mismo valor en débitos y créditos.")
    return "\n".join(out)


# ---------------------------------------------------------------- Proyectos
def _proyectos(tablas, pregunta):
    flujos, tasa, fuente_tasa = None, None, "supuesto por defecto (12 %)"
    for df in tablas.values():
        for c in df.columns:
            if "flujo" in _n(c) and _num(df[c]).notna().sum() >= 2:
                flujos = _num(df[c]).dropna().tolist()
        for _, fila in df.iterrows():
            txt = " ".join(str(v) for v in fila.tolist())
            if "tasa" in _n(txt) or "descuento" in _n(txt):
                m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", txt)
                if m:
                    tasa, fuente_tasa = float(m.group(1).replace(",", ".")) / 100, "tomada del documento"
    if not flujos:
        return "No encontré una columna de **flujos** (por ejemplo `flujo_neto`). El primer valor debe ser la inversión inicial, negativa."
    if tasa is None:
        tasa = 0.12
    r = vpn_tir(flujos, tasa)
    tir = None if r["tir"] is None else r["tir"]
    out = ["### Hallazgos",
           f"- Inversión inicial: **{_m(flujos[0])}** · Horizonte: **{len(flujos) - 1} períodos**",
           f"- Tasa de descuento: **{tasa * 100:.1f} %** ({fuente_tasa})",
           f"- VPN: **{_m(r['vpn'])}**", f"- TIR: **{'—' if tir is None else f'{tir * 100:.1f} %'}**",
           f"- Recuperación de la inversión: **{'—' if r['payback_periodos'] is None else f'{r['payback_periodos']:.1f} períodos'}**",
           f"- Decisión: **{r['decision']}**", "\n### Sensibilidad del VPN a la tasa"]
    filas = []
    for t in [tasa - 0.04, tasa - 0.02, tasa, tasa + 0.02, tasa + 0.04, tasa + 0.08]:
        if t > 0:
            filas.append((f"{t * 100:.1f} %", _fmt(vpn_tir(flujos, t)["vpn"])))
    out.append(_tabla(["Tasa", "VPN"], filas))
    out.append("\n### Interpretación")
    if tir is not None:
        out.append(f"- La TIR ({tir * 100:.1f} %) {'supera' if tir > tasa else 'no supera'} la tasa de descuento ({tasa * 100:.1f} %), "
                   f"por eso el proyecto {'crea' if tir > tasa else 'destruye'} valor.")
    out.append("- Revisa los supuestos de ventas y costos: pequeñas variaciones cambian el VPN (ver tabla de sensibilidad).")
    return "\n".join(out)


# ---------------------------------------------------------------- Diagnóstico
def _diagnostico(tablas, pregunta):
    datos, anios = {}, []
    for df in tablas.values():
        if len(df.columns) < 2:
            continue
        cols = list(df.columns[1:])
        for c in cols:
            if str(c) not in anios:
                anios.append(str(c))
        for _, f in df.iterrows():
            datos[_n(f.iloc[0])] = {str(c): pd.to_numeric(f[c], errors="coerce") for c in cols}
    if not any(k in datos for k in ("total activo", "total pasivo", "total patrimonio")):
        return "No encontré un balance con filas como *Total activo*, *Total pasivo* y *Total patrimonio*."

    def val(claves, y):
        for k in claves:
            v = datos.get(k, {}).get(y)
            if v is not None and pd.notna(v):
                return float(v)
        return None

    res = {}
    for y in anios:
        res[y] = razones_financieras(
            activo_corriente=val(["total activo corriente"], y), pasivo_corriente=val(["total pasivo corriente"], y),
            inventarios=val(["inventarios"], y), activo_total=val(["total activo"], y), pasivo_total=val(["total pasivo"], y),
            patrimonio=val(["total patrimonio"], y), ventas=val(["ventas netas", "ventas", "ingresos"], y),
            costo_ventas=val(["costo de ventas"], y), utilidad_neta=val(["utilidad neta"], y))

    nombres = {"razon_corriente": ("Razón corriente", 2, False), "prueba_acida": ("Prueba ácida", 2, False),
               "endeudamiento": ("Endeudamiento", 1, True), "apalancamiento": ("Apalancamiento (pasivo/patrimonio)", 2, False),
               "margen_bruto": ("Margen bruto", 1, True), "margen_neto": ("Margen neto", 1, True),
               "ROA": ("ROA", 1, True), "ROE": ("ROE", 1, True), "rotacion_activos": ("Rotación de activos", 2, False)}
    filas = []
    for k, (nom, dec, pct) in nombres.items():
        if any(k in res[y] for y in anios):
            filas.append([nom] + [("—" if k not in res[y] else (f"{res[y][k] * 100:.{dec}f} %" if pct else f"{res[y][k]:.{dec}f}")) for y in anios])
    out = ["### Indicadores", _tabla(["Indicador"] + anios, filas), "\n### Interpretación"]

    ult, ant = anios[-1], (anios[-2] if len(anios) > 1 else None)
    r = res[ult]
    rc = r.get("razon_corriente")
    if rc is not None:
        out.append(f"- **Liquidez:** razón corriente de {rc:.2f} → " + ("riesgo de no poder pagar deudas de corto plazo." if rc < 1 else "ajustada." if rc < 1.5 else "holgada."))
    pa = r.get("prueba_acida")
    if pa is not None and pa < 1:
        out.append(f"- La prueba ácida ({pa:.2f}) indica dependencia de vender inventario para pagar deudas.")
    e = r.get("endeudamiento")
    if e is not None:
        out.append(f"- **Endeudamiento:** {e * 100:.1f} % de los activos está financiado con deuda → " + ("alto." if e > .6 else "moderado." if e >= .4 else "bajo."))
    if ant:
        def cambio(claves):
            a, b = val(claves, ant), val(claves, ult)
            return None if not a or b is None else (b - a) / abs(a) * 100
        cv, ci, cc = cambio(["ventas netas", "ventas", "ingresos"]), cambio(["inventarios"]), cambio(["cuentas por cobrar"])
        if cv is not None:
            out.append(f"- **Ventas:** {cv:+.1f} % frente a {ant}.")
        if ci is not None and cv is not None and ci > cv:
            out.append(f"- Los inventarios crecen más rápido ({ci:+.1f} %) que las ventas: capital inmovilizado.")
        if cc is not None and cv is not None and cc > cv:
            out.append(f"- Las cuentas por cobrar crecen más rápido ({cc:+.1f} %) que las ventas: revisar la política de cartera.")
        if res[ant].get("razon_corriente") and rc and rc < res[ant]["razon_corriente"]:
            out.append(f"- La liquidez empeoró frente a {ant} ({res[ant]['razon_corriente']:.2f} → {rc:.2f}).")
    out.append("\n### Recomendaciones\n- Acelerar el cobro de cartera y ajustar las compras para reducir inventario.\n"
               "- Vigilar el endeudamiento y los gastos financieros frente a la utilidad operacional.")
    return "\n".join(out)


# ---------------------------------------------------------------- Proyecciones
def _proyecciones(tablas, pregunta):
    mejor = None
    for df in tablas.values():
        if len(df.columns) < 2:
            continue
        for c in df.columns[1:]:
            if _num(df[c]).notna().sum() >= 6:
                if mejor is None or any(w in _n(c) for w in ("venta", "demanda", "unidad", "valor")):
                    mejor = (df, c)
    if mejor is None:
        return "No encontré una serie numérica con al menos 6 datos para proyectar."
    df, col = mejor
    y = _num(df[col]).dropna()
    m = re.search(r"(\d+)\s*(mes|per[ií]odo|trimestre|a[nñ]o)", _n(pregunta))
    h = int(m.group(1)) if m else 6
    fechas = pd.to_datetime(df.iloc[:, 0], errors="coerce")
    mensual = fechas.notna().all() and len(df) > 1 and (fechas.diff().dropna().dt.days.between(27, 32).mean() > .8)
    s = 12 if (mensual and len(y) >= 24) else 0
    r = proyectar_serie(y.tolist(), h, s)
    if "error" in r:
        return r["error"]
    etiquetas = ([(fechas.iloc[-1] + pd.DateOffset(months=i + 1)).strftime("%Y-%m") for i in range(h)] if mensual
                 else [f"Período +{i + 1}" for i in range(h)])
    out = ["### Hallazgos", f"- Serie analizada: **{col}** ({len(y)} datos) · Último valor: **{_fmt(y.iloc[-1])}**",
           f"- Tendencia estimada: **{_fmt(r['tendencia_por_periodo'])} por período**",
           f"- Estacionalidad: **{'sí (12 períodos)' if s else 'no detectada / datos insuficientes'}**",
           f"- Error relativo del modelo en los datos históricos: **{r['error_relativo_%']} %**", "\n### Pronóstico",
           _tabla(["Período", "Pronóstico"], [(e, _fmt(v)) for e, v in zip(etiquetas, r["pronostico"])]),
           "\n### Interpretación"]
    if s and h <= 12:
        ref, txt = y.iloc[len(y) - 12 + h - 1], "frente al mismo período del año anterior"
    else:
        ref, txt = y.iloc[-1], "frente al último dato"
    cambio = (r["pronostico"][-1] - ref) / ref * 100
    out.append(f"- Al final del horizonte el modelo proyecta **{cambio:+.1f} %** {txt}.")
    out.append("- Error bajo (menos de 5 %) indica un pronóstico confiable; es una estimación estadística, no una garantía." if r["error_relativo_%"] < 5
               else "- El error histórico es alto: el pronóstico es menos confiable, conviene revisar los datos.")
    return "\n".join(out)


AGENTES_LOCALES = {"contabilidad": _contabilidad, "proyectos": _proyectos, "diagnostico": _diagnostico, "proyecciones": _proyecciones}


def ejecutar_local(area: str, tablas: dict, pregunta: str = "") -> str:
    if not tablas:
        return "El modo sin IA solo puede leer **CSV y Excel**. Para PDF o TXT necesitas la clave de la API."
    return AGENTES_LOCALES[area](tablas, pregunta)
