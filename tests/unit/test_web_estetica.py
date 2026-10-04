"""Comprobaciones automáticas de la estética de la web.

Cubren la parte verificable por código de la lista "que no parezca hecha por
una IA" (D-037) y de las reglas del proyecto: paleta cerrada, esquinas
rectas, sin sombras ni degradados, fuentes propias con su licencia y respeto a
prefers-reduced-motion.
"""

import re

import pytest

from tasador.config import RUTA_WEB

CSS = (RUTA_WEB / "css" / "estilo.css").read_text(encoding="utf-8")
HTML = (RUTA_WEB / "index.html").read_text(encoding="utf-8")
PALETA = {"#060a06", "#33ff66", "#1f9d45", "#0f3d1c"}
FUENTES = (
    "WebPlus_IBM_VGA_9x16.woff",
    "IBMPlexMono-Regular.woff2",
    "IBMPlexMono-Bold.woff2",
)
LICENCIAS = ("LICENCIA-oldschool-pc-font-pack.txt", "LICENCIA-ibm-plex.txt", "CREDITOS.txt")


def css_sin_comentarios() -> str:
    return re.sub(r"/\*.*?\*/", "", CSS, flags=re.DOTALL)


# Paleta y colores


def test_solo_colores_de_la_paleta_aprobada():
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
