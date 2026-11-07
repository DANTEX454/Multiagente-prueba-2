"""Convierte los documentos subidos (CSV, Excel, PDF, TXT) en texto para los agentes."""
import io
import pandas as pd
from pypdf import PdfReader

LIMITE = 20000  # caracteres máximos que se envían al modelo


def leer_archivo(nombre: str, datos: bytes) -> str:
    ext = nombre.lower().rsplit(".", 1)[-1]

    if ext == "csv":
        df = pd.read_csv(io.BytesIO(datos), sep=None, engine="python")
        return f"Archivo CSV ({len(df)} filas)\n{df.to_csv(index=False)}"[:LIMITE]

    if ext in ("xlsx", "xls"):
        hojas = pd.read_excel(io.BytesIO(datos), sheet_name=None)
        partes = [f"Hoja: {n} ({len(d)} filas)\n{d.to_csv(index=False)}" for n, d in hojas.items()]
        return "\n\n".join(partes)[:LIMITE]

    if ext == "pdf":
        lector = PdfReader(io.BytesIO(datos))
        return "\n".join((p.extract_text() or "") for p in lector.pages)[:LIMITE]

    if ext == "txt":
        return datos.decode("utf-8", "ignore")[:LIMITE]

    raise ValueError(f"Formato no soportado: .{ext}")


def leer_tablas(nombre: str, datos: bytes) -> dict:
    """Devuelve las tablas del archivo como DataFrames (solo CSV y Excel). Lo usa el modo sin IA."""
    ext = nombre.lower().rsplit(".", 1)[-1]
    try:
        if ext == "csv":
            return {"datos": pd.read_csv(io.BytesIO(datos), sep=None, engine="python")}
        if ext in ("xlsx", "xls"):
            return pd.read_excel(io.BytesIO(datos), sheet_name=None)
    except Exception:
        pass
    return {}
