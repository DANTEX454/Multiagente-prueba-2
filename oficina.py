"""Oficina virtual estilo 8 bits: el gerente recibe el documento y se lo lleva al empleado del área."""
from html import escape
import unicodedata


def _sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

# ---------- Sprites (cada letra = un píxel) ----------
HEAD = [
    "..HHHHHH..",
    ".HHHHHHHH.",
    ".HSSSSSSH.",
    ".SSKSSKSS.",
    ".SSSSSSSS.",
    "..SSMMSS..",
    "...SSSS...",
]
TORSO = [".BBBBBBBB.", "BBBBBBBBBB", "BBBBBBBBBB", "BBBBBBBBBB"]
TORSO_JEFE = [".BBBTTBBB.", "BBBBTTBBBB", "BBBBTTBBBB", "BBBBTTBBBB"]
PAPEL = ["KKKKKK", "KWWWWK", "KWGGWK", "KWWWWK", "KWGGWK", "KWWWWK", "KKKKKK"]
CHECK = ["....V", "...V.", "V.V..", ".V..."]
PLANTA = ["..L.L..", ".LLLLL.", "..LLL..", "...L...", ".OOOOO.", ".OOOOO.", "..OOO.."]

AREAS = {
    "contabilidad": {"nombre": "Contabilidad", "cx": 32,  "camisa": "#3b82f6", "pelo": "#4a3222"},
    "proyectos":    {"nombre": "Proyectos",    "cx": 96,  "camisa": "#22c55e", "pelo": "#1a1a1a"},
    "diagnostico":  {"nombre": "Diagnóstico",  "cx": 160, "camisa": "#f59e0b", "pelo": "#8a5a2b"},
    "proyecciones": {"nombre": "Proyecciones", "cx": 224, "camisa": "#a855f7", "pelo": "#d9531e"},
}
GER_CX, GER_OY, EMP_OY = 128, 20, 70


def pix(grid, ox, oy, pal, s=1):
    """Dibuja un sprite como rectángulos, uniendo píxeles contiguos del mismo color."""
    out = []
    for r, fila in enumerate(grid):
        c = 0
        while c < len(fila):
            ch = fila[c]
            if ch == ".":
                c += 1
                continue
            j = c
            while j < len(fila) and fila[j] == ch:
                j += 1
            out.append(f'<rect x="{ox + c * s}" y="{oy + r * s}" width="{(j - c) * s}" height="{s}" fill="{pal[ch]}"/>')
            c = j
    return "".join(out)


def burbuja(cx, y, texto, puntos=False):
    w = max(18, len(texto) * 4 + 6) if not puntos else 20
    x = cx - w / 2
    t = (f'<text class="px" x="{cx}" y="{y + 6.3}" text-anchor="middle" font-size="4" fill="#111">{escape(texto)}</text>'
         if not puntos else
         "".join(f'<rect class="pt" style="animation-delay:{i * .25}s" x="{cx - 5 + i * 5}" y="{y + 3.5}" width="2" height="2" fill="#111"/>' for i in range(3)))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="9" fill="#111"/><rect x="{x + 1}" y="{y + 1}" width="{w - 2}" height="7" fill="#fff"/>'
            f'<rect x="{cx - 2}" y="{y + 9}" width="5" height="1" fill="#111"/><rect x="{cx - 1}" y="{y + 8}" width="3" height="1" fill="#fff"/>'
            f'<rect x="{cx - 1}" y="{y + 10}" width="3" height="1" fill="#111"/><rect x="{cx}" y="{y + 11}" width="1" height="1" fill="#111"/>'
            f'<rect x="{cx - 1}" y="{y + 9}" width="3" height="1" fill="#fff"/>{t}')


def persona(cx, oy, nombre, camisa, pelo, estado, texto="", jefe=False):
    """estado: i (quieto) | w (trabajando) | d (terminado)"""
    ox = cx - 5
    pal = {"H": pelo, "S": "#f2c9a0", "K": "#1a1a1a", "M": "#b5483a", "B": camisa, "T": "#e11d48", "V": "#38d66b"}
    cuerpo = pix(HEAD, ox, oy, pal) + pix(TORSO_JEFE if jefe else TORSO, ox, oy + 7, pal)
    portatil = (f'<rect x="{ox + 1}" y="{oy + 8}" width="8" height="3" fill="#aab4c0"/><rect x="{ox + 1}" y="{oy + 8}" width="8" height="1" fill="#dde3ea"/>'
                f'<rect class="logo" x="{ox + 4}" y="{oy + 9}" width="2" height="1" fill="#fff"/>')
    manos = (f'<rect class="hl" x="{ox - 1}" y="{oy + 9}" width="2" height="2" fill="#f2c9a0"/>'
             f'<rect class="hr" x="{ox + 9}" y="{oy + 9}" width="2" height="2" fill="#f2c9a0"/>')
    escritorio = (f'<rect x="{ox - 4}" y="{oy + 11}" width="18" height="1" fill="#e0a96d"/><rect x="{ox - 4}" y="{oy + 12}" width="18" height="2" fill="#9c6b3a"/>'
                  f'<rect x="{ox - 3}" y="{oy + 14}" width="2" height="3" fill="#5a3a1a"/><rect x="{ox + 11}" y="{oy + 14}" width="2" height="3" fill="#5a3a1a"/>')
    foco = f'<rect class="foco" x="{cx - 30}" y="{oy - 10}" width="60" height="38" fill="#fff" opacity=".10"/>' if estado == "w" else ""
    nombre_svg = (f'<text class="px" x="{cx + .4}" y="{oy + 22.4}" text-anchor="middle" font-size="3.6" fill="#000">{escape(_sin_tildes(nombre).upper())}</text>'
                  f'<text class="px" x="{cx}" y="{oy + 22}" text-anchor="middle" font-size="3.6" fill="#fff">{escape(_sin_tildes(nombre).upper())}</text>')
    check = pix(CHECK, ox + 12, oy - 1, pal, 2) if estado == "d" else ""
    bub = burbuja(cx, oy - 14, texto, puntos=(estado == "w" and not texto)) if (texto or estado == "w") else ""
    return (f'{foco}<g class="{estado}"><g class="body">{cuerpo}</g>{portatil}{manos}{escritorio}</g>{nombre_svg}'
            f'<g class="chk">{check}</g>{bub}')


def html_oficina(estado="espera", area=None, mensaje=""):
    """estado: espera | gerente | area | listo"""
    partes = []
    nom = AREAS[area]["nombre"] if area else ""
    g_est = "w" if estado == "gerente" else "i"
    g_txt = {"espera": "SUBE UN DOCUMENTO", "gerente": "LEYENDO...", "area": f"A {_sin_tildes(nom).upper()}", "listo": "TRABAJO TERMINADO"}[estado]
    partes.append(persona(GER_CX, GER_OY, "Gerente", "#334155", "#1a1a1a", g_est, g_txt, jefe=True))

    vuelo = ""
    for clave, a in AREAS.items():
        est, txt = "i", ""
        if clave == area and estado == "area":
            est = "w"
        elif clave == area and estado == "listo":
            est, txt = "d", "¡LISTO!"
        partes.append(persona(a["cx"], EMP_OY, a["nombre"], a["camisa"], a["pelo"], est, txt))
        if clave == area and estado == "area":
            vuelo = (f"@keyframes vuelo{{from{{transform:translate({GER_CX + 6}px,{GER_OY + 4}px)}}"
                     f"to{{transform:translate({a['cx'] + 4}px,{EMP_OY + 4}px)}}}}")

    papel_pal = {"K": "#111", "W": "#fff", "G": "#9aa4b0"}
    if estado == "gerente":
        partes.append(f'<g class="lee" transform="translate({GER_CX + 6},{GER_OY + 4})">{pix(PAPEL, 0, 0, papel_pal)}</g>')
    elif estado == "area" and area:
        partes.append(f'<g class="vuela">{pix(PAPEL, 0, 0, papel_pal)}</g>')

    hud_txt = {"espera": "ESPERANDO DOCUMENTO", "gerente": "GERENTE REVISANDO",
               "area": f"{_sin_tildes(nom).upper()} TRABAJANDO", "listo": "MISION COMPLETA!"}[estado]
    llenos = {"espera": 0, "gerente": 3, "area": 7, "listo": 10}[estado]
    bloques = "".join(
        f'<rect class="{"ult" if (i == llenos - 1 and estado != "listo") else ""}" x="{190 + i * 6}" y="118" width="5" height="5" fill="{"#38d66b" if i < llenos else "#333"}"/>'
        for i in range(10))

    return f'''<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<style>
body{{margin:0;background:transparent;overflow:hidden}}
svg{{width:100%;max-width:960px;height:auto;display:block;margin:0 auto;image-rendering:pixelated;border:4px solid #111;box-sizing:border-box;border-radius:4px}}
.px{{font-family:'Press Start 2P',monospace;text-rendering:optimizeSpeed}}
.w .body{{animation:bob .4s steps(1) infinite}}
.w .hl{{animation:mano .3s steps(1) infinite}}
.w .hr{{animation:mano .3s .15s steps(1) infinite}}
.w .logo{{animation:parp .5s steps(1) infinite}}
.i .body{{animation:bob 1.6s steps(1) infinite}}
.foco{{animation:parp 1s steps(1) infinite}}
.pt{{animation:salto .9s steps(1) infinite}}
.chk{{animation:parp .6s steps(1) infinite}}
.ult{{animation:parp .5s steps(1) infinite}}
.lee{{animation:bob .8s steps(1) infinite}}
.vuela{{animation:vuelo 1.2s steps(10) forwards}}
@keyframes bob{{50%{{transform:translateY(1px)}}}}
@keyframes mano{{50%{{transform:translateY(-1px)}}}}
@keyframes parp{{50%{{opacity:0}}}}
@keyframes salto{{0%,100%{{transform:translateY(0)}}33%{{transform:translateY(-1.5px)}}}}
{vuelo}
</style></head><body>
<svg viewBox="0 0 256 128" shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">
<defs><pattern id="suelo" width="16" height="16" patternUnits="userSpaceOnUse"><rect width="16" height="16" fill="#8b6f47"/><rect width="8" height="8" fill="#7a5f3b"/><rect x="8" y="8" width="8" height="8" fill="#7a5f3b"/></pattern></defs>
<rect width="256" height="128" fill="#2a3a6e"/><rect y="0" width="256" height="52" fill="#34498f"/><rect y="50" width="256" height="2" fill="#111"/>
<rect y="52" width="256" height="60" fill="url(#suelo)"/>
<rect x="28" y="18" width="28" height="22" fill="#111"/><rect x="30" y="20" width="24" height="18" fill="#7dd3fc"/><rect x="41" y="20" width="2" height="18" fill="#111"/><rect x="30" y="28" width="24" height="2" fill="#111"/>
<rect x="200" y="18" width="28" height="22" fill="#111"/><rect x="202" y="20" width="24" height="18" fill="#7dd3fc"/><rect x="213" y="20" width="2" height="18" fill="#111"/><rect x="202" y="28" width="24" height="2" fill="#111"/>
<rect x="236" y="6" width="12" height="12" fill="#111"/><rect x="237" y="7" width="10" height="10" fill="#fff"/><rect x="241" y="9" width="1" height="4" fill="#111"/><rect x="241" y="12" width="3" height="1" fill="#111"/>
{pix(PLANTA, 6, 98, {"L": "#2fbf5b", "O": "#b45309"})}{pix(PLANTA, 243, 98, {"L": "#2fbf5b", "O": "#b45309"})}
<text class="px" x="6" y="9" font-size="5" fill="#ffd166">OFICINA 8-BIT</text>
{''.join(partes)}
<rect y="112" width="256" height="16" fill="#111"/><rect y="112" width="256" height="1" fill="#ffd166"/>
<text class="px" x="6" y="122.5" font-size="4.4" fill="#fff">{escape(hud_txt)}</text>{bloques}
</svg></body></html>'''
