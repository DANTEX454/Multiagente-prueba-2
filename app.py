"""Interfaz: streamlit run app.py"""
import time
import streamlit as st
import streamlit.components.v1 as components
from lector import leer_archivo, leer_tablas
from gerente import decidir_area
from agentes import ejecutar_agente, AGENTES, CLAVE
from modo_local import clasificar_local, ejecutar_local
from oficina import html_oficina, duracion_area

st.set_page_config(page_title="Oficina Virtual", page_icon="🏢", layout="wide")
st.title("🏢 Oficina Virtual")

with st.sidebar:
    st.header("⚙️ Modo de trabajo")
    forzar_local = st.checkbox("Modo sin IA (solo cálculos)", value=not CLAVE, disabled=not CLAVE,
                               help="Calcula con Python y reglas fijas. No usa la API ni genera costos.")
    if not CLAVE:
        st.info("No hay clave de API configurada: la app trabaja en modo sin IA (solo CSV y Excel).")
    else:
        st.caption("Con IA, el gerente y los agentes interpretan el documento con Claude. Sin IA, solo se calculan los indicadores.")

usar_ia = bool(CLAVE) and not forzar_local
oficina = st.empty()


def mostrar(estado="espera", area=None, mensaje=""):
    with oficina.container():
        components.html(html_oficina(estado, area, mensaje), height=610)


mostrar()

archivo = st.file_uploader("Sube un documento (CSV, Excel, PDF o TXT)", type=["csv", "xlsx", "xls", "pdf", "txt"])
pregunta = st.text_input("¿Qué necesitas? (opcional)", placeholder="Ej: proyecta las ventas de los próximos 6 meses")


def esperar(desde, minimo):
    """Deja que la animación se vea completa aunque el cálculo termine rápido."""
    resto = minimo - (time.time() - desde)
    if resto > 0:
        time.sleep(resto)


def aviso_ia(e):
    st.warning("No pude usar la IA (revisa la clave en Secrets). Continúo en modo sin IA.")
    with st.expander("Detalle técnico"):
        st.code(f"{type(e).__name__}: {str(e)[:300]}")


if st.button("Enviar al gerente", type="primary", disabled=archivo is None):
    datos = archivo.getvalue()
    tablas = leer_tablas(archivo.name, datos)

    t0 = time.time()
    mostrar("gerente", mensaje="Revisando el documento…")
    decision, documento = None, ""
    if usar_ia:
        try:
            documento = leer_archivo(archivo.name, datos)
            decision = decidir_area(documento, pregunta)
        except Exception as e:
            aviso_ia(e)
            usar_ia = False
    if decision is None:
        decision = clasificar_local(tablas, pregunta)

    esperar(t0, 2.8)
    area = decision["area"]
    st.info(f"🧑‍💼 Gerente → {AGENTES[area]['emoji']} **{AGENTES[area]['nombre']}**: {decision['razon']}")
    mostrar("area", area)
    t1 = time.time()

    respuesta = None
    if usar_ia:
        estado = st.empty()
        try:
            respuesta = ejecutar_agente(area, documento, pregunta, avisar=estado.caption)
        except Exception as e:
            aviso_ia(e)
        estado.empty()
    if respuesta is None:
        respuesta = ejecutar_local(area, tablas, pregunta)
        st.caption("📐 Modo sin IA: resultados calculados con Python.")

    esperar(t1, duracion_area(area) + 0.8)
    mostrar("listo", area, "¡Listo!")
    st.markdown(respuesta)
