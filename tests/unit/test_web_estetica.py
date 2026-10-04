"""Comprobaciones automáticas de la estética de la web.

Cubren la parte verificable por código de la lista "que no parezca hecha por
una IA" (D-037) y de las reglas del proyecto: paleta cerrada, esquinas
rectas, sin sombras ni degradados, fuentes propias con su licencia y respeto a
prefers-reduced-motion.
"""

import re
import struct

import build_og_image
import pytest

from tasador.config import RUTA_WEB

CSS = (RUTA_WEB / "css" / "estilo.css").read_text(encoding="utf-8")
HTML = (RUTA_WEB / "index.html").read_text(encoding="utf-8")
# Paleta VGA de 16 colores (D-039): ningún color fuera de ella
PALETA = {
    "#000000",
    "#0000aa",
    "#00aa00",
    "#00aaaa",
    "#aa0000",
    "#aa00aa",
    "#aa5500",
    "#aaaaaa",
    "#555555",
    "#5555ff",
    "#55ff55",
    "#55ffff",
    "#ff5555",
    "#ff55ff",
    "#ffff55",
    "#ffffff",
}
FUENTES = (
    "WebPlus_IBM_VGA_9x16.woff",
    "IBMPlexMono-Regular.woff2",
    "IBMPlexMono-Bold.woff2",
)
LICENCIAS = ("LICENCIA-oldschool-pc-font-pack.txt", "LICENCIA-ibm-plex.txt", "CREDITOS.txt")


def css_sin_comentarios() -> str:
    return re.sub(r"/\*.*?\*/", "", CSS, flags=re.DOTALL)


# Paleta y colores


def test_solo_colores_de_la_paleta_vga():
    colores = set(re.findall(r"#[0-9a-fA-F]{3,8}\b", css_sin_comentarios()))
    assert {color.lower() for color in colores} <= PALETA


def test_sin_colores_con_nombre_ni_funciones_de_color():
    css = css_sin_comentarios()
    assert not re.search(r"\b(rgb|rgba|hsl|hsla|oklch|lab)\(", css)
    for nombre in ("purple", "violet", "indigo", "blue", "white", "gray", "grey"):
        assert not re.search(rf":\s*{nombre}\b", css), nombre


def test_el_favicon_usa_la_paleta():
    favicon = (RUTA_WEB / "favicon.svg").read_text(encoding="utf-8")
    assert set(re.findall(r"#[0-9a-fA-F]{6}", favicon)) <= PALETA
    assert 'href="favicon.svg"' in HTML


# Prohibiciones de la lista anti-IA


def test_esquinas_rectas():
    for valor in re.findall(r"border-radius\s*:\s*([^;]+);", css_sin_comentarios()):
        assert valor.strip() == "0"


@pytest.mark.parametrize(
    "prohibido",
    [
        "box-shadow",
        "text-shadow",
        "drop-shadow",
        "gradient(",
        "backdrop-filter",
        "blur(",
        "filter:",
        "transition",
    ],
)
def test_sin_sombras_degradados_desenfoques_ni_transiciones(prohibido):
    assert prohibido not in css_sin_comentarios()


@pytest.mark.parametrize(
    "fuente", ["Inter", "system-ui", "Roboto", "Helvetica", "Arial", "sans-serif", "-apple-system"]
)
def test_sin_tipografias_genericas(fuente):
    assert fuente not in css_sin_comentarios()


def test_sin_iconos_de_librerias_ni_cdn():
    texto = HTML + CSS
    for marca in ("lucide", "heroicons", "fontawesome", "font-awesome", "googleapis", "cdn"):
        assert marca not in texto.lower(), marca


def test_las_unicas_animaciones_son_el_parpadeo_del_cursor():
    nombres = set(re.findall(r"animation\s*:\s*([a-z-]+)", css_sin_comentarios()))
    assert nombres <= {"parpadeo", "none"}
    assert set(re.findall(r"@keyframes\s+([a-z-]+)", CSS)) == {"parpadeo"}


def test_movimiento_reducido_desactiva_el_parpadeo():
    bloque = CSS[CSS.index("@media (prefers-reduced-motion: reduce)") :]
    assert "animation: none" in bloque
    arbol = (RUTA_WEB / "js" / "arbol.js").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in arbol


# Fuentes alojadas con su licencia


@pytest.mark.parametrize("archivo", FUENTES + LICENCIAS)
def test_fuentes_y_licencias_presentes(archivo):
    assert (RUTA_WEB / "fuentes" / archivo).is_file()


def test_cada_font_face_apunta_a_un_archivo_existente():
    rutas = re.findall(r'url\("\.\./fuentes/([^"]+)"\)', CSS)
    assert set(rutas) == set(FUENTES)


def test_atribucion_de_la_fuente_cc_by_sa_en_el_pie():
    assert "VileR" in HTML
    assert "https://int10h.org/oldschool-pc-fonts/" in HTML


# Metadatos


def test_metadatos_para_compartir():
    for propiedad in ("og:title", "og:description", "og:type", "og:url"):
        assert f'property="{propiedad}"' in HTML
    assert '<meta name="description"' in HTML


# Imagen para compartir


FIRMA_PNG = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])


def dimensiones_png(ruta) -> tuple[int, int]:
    """Ancho y alto leídos de la cabecera IHDR del PNG."""
    cabecera = ruta.read_bytes()[:24]
    assert cabecera[:8] == FIRMA_PNG
    return struct.unpack(">II", cabecera[16:24])


def test_imagen_para_compartir_existe_y_mide_1200x630():
    assert dimensiones_png(RUTA_WEB / "og.png") == (1200, 630)
    assert 'property="og:image" content="https://ml-vivienda-madrid-1.onrender.com/og.png"' in HTML
    assert 'name="twitter:card" content="summary_large_image"' in HTML


def test_imagen_para_compartir_al_dia_y_determinista(tmp_path):
    for nombre in ("a.png", "b.png"):
        build_og_image.construir_imagen(build_og_image.RUTA_FUENTE).save(
            tmp_path / nombre, format="PNG", optimize=True
        )
    generada = (tmp_path / "a.png").read_bytes()
    assert generada == (tmp_path / "b.png").read_bytes()
    assert generada == (RUTA_WEB / "og.png").read_bytes()


def test_logo_de_la_imagen_igual_que_el_de_la_web():
    bloque = re.search(r'<pre class="logo-ascii" aria-hidden="true">(.*?)</pre>', HTML, re.DOTALL)
    assert bloque is not None
    assert tuple(bloque.group(1).splitlines()) == build_og_image.LOGO


def test_imagen_usa_solo_la_paleta():
    colores = set()
    for nombre in ("NEGRO", "GRIS", "TEXTO", "AMARILLO", "VERDE", "CIAN"):
        colores.add(getattr(build_og_image, nombre))
    assert colores <= PALETA
