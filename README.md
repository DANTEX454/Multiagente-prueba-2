# 🏢 Oficina Virtual (8 bits): gerente + 4 áreas

El gerente recibe el documento y lo envía al área adecuada:
📒 Contabilidad · 📐 Proyectos · 🩺 Diagnóstico · 📈 Proyecciones

- **Con clave de API de Anthropic:** Claude interpreta el documento y redacta el análisis.
- **Sin clave (modo sin IA):** calcula con Python y entrega el reporte. Solo CSV y Excel.

## Publicar en Streamlit Community Cloud
1. Sube TODOS estos archivos a la raíz de un repositorio de GitHub.
2. En share.streamlit.io: Create app -> repositorio, rama main, archivo app.py.
3. (Opcional) En Advanced settings -> Secrets: `ANTHROPIC_API_KEY = "sk-ant-..."`
   Sin esa línea la app funciona igual en modo sin IA.

## Archivos
app.py (interfaz) · oficina.py (escena 8 bits) · gerente.py · agentes.py · calculos.py
modo_local.py (modo sin IA) · lector.py · requirements.txt · ventas_demo.csv
