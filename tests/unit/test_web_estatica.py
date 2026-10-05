"""Tests de los archivos estáticos de la web: traducciones, HTML y textos."""

import json
import re

import pytest

from tasador.config import RUTA_WEB
from tasador.domain.reglas import TIPOS_CASA_O_CHALET
from tasador.schemas.errores import CodigoError
from tasador.services.metadata import construir_metadata

IDIOMAS = ("es", "en")
# Códigos que solo genera la web (no la API)
CODIGOS_DEL_CLIENTE = ("RED", "DESCONOCIDO")
PATRON_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿\U0001f000-\U0001f2ff]")


def diccionario(idioma: str) -> dict:
    return json.loads((RUTA_WEB / "i18n" / f"{idioma}.json").read_text(encoding="utf-8"))


def claves_planas(datos: dict, prefijo: str = "") -> set[str]:
    claves = set()
    for clave, valor in datos.items():
        completa = f"{prefijo}{clave}"
        if isinstance(valor, dict):
            claves |= claves_planas(valor, f"{completa}.")
        else:
            claves.add(completa)
    return claves


def test_es_y_en_tienen_exactamente_las_mismas_claves():
    assert claves_planas(diccionario("es")) == claves_planas(diccionario("en"))


@pytest.mark.parametrize("idioma", IDIOMAS)
def test_todos_los_valores_son_texto_no_vacio(idioma):
    datos = diccionario(idioma)
    for clave in claves_planas(datos):
        valor = datos
        for parte in clave.split("."):
            valor = valor[parte]
        assert isinstance(valor, str)
        assert valor.strip(), clave


@pytest.mark.parametrize("idioma", IDIOMAS)
def test_cada_codigo_de_error_tiene_traduccion(idioma):
    errores = diccionario(idioma)["errores"]
    for codigo in CodigoError:
        assert codigo.value in errores
    for codigo in CODIGOS_DEL_CLIENTE:
        assert codigo in errores


def test_cada_data_i18n_del_html_existe_en_el_diccionario():
    html = (RUTA_WEB / "index.html").read_text(encoding="utf-8")
    claves_html = set(re.findall(r'data-i18n="([^"]+)"', html))
    assert claves_html
    assert claves_html <= claves_planas(diccionario("es"))


def test_cada_clave_usada_en_el_javascript_existe():
    claves = claves_planas(diccionario("es"))
    usadas = set()
    for archivo in (RUTA_WEB / "js").glob("*.js"):
        texto = archivo.read_text(encoding="utf-8")
        usadas |= set(re.findall(r'\bt\("([a-z_]+\.[a-z_.]+)"', texto))
        usadas |= set(re.findall(r'anotar\("([a-z_]+\.[a-z_.]+)"', texto))
    assert usadas
    assert usadas <= claves


def test_cada_campo_del_html_tiene_etiqueta_del_catalogo():
    html = (RUTA_WEB / "index.html").read_text(encoding="utf-8")
    nombres_html = set(re.findall(r'data-etiqueta-campo="([^"]+)"', html))
    nombres_catalogo = set()
    for campo in construir_metadata().fields:
        nombres_catalogo.add(campo.name)
    assert nombres_html == nombres_catalogo


def test_sin_emojis_en_la_web():
    for archivo in RUTA_WEB.rglob("*"):
        if archivo.suffix in {".html", ".js", ".css", ".json"}:
            assert not PATRON_EMOJI.search(archivo.read_text(encoding="utf-8")), archivo.name


def test_sin_recursos_de_terceros_en_el_html():
    """Todo lo que el navegador descarga (scripts, estilos, fuentes, iconos) es local.

    Los enlaces <a> del pie pueden apuntar fuera: no se cargan al abrir la página.
    """
    html = (RUTA_WEB / "index.html").read_text(encoding="utf-8")
    recursos = re.findall(r'src="([^"]+)"', html)
    recursos += re.findall(r'<link[^>]*href="([^"]+)"', html)
    assert recursos
    for recurso in recursos:
        assert not recurso.startswith(("http://", "https://", "//")), recurso


def test_metadata_marca_las_casas_y_chalets():
    for tipo in construir_metadata().property_types:
        assert tipo.is_house == (tipo.value in TIPOS_CASA_O_CHALET)


# Usabilidad del formulario (D-042). Sin ejecutor de JavaScript en el proyecto,
# se comprueba el código fuente; el comportamiento se verificó en Chrome.


def test_desplegable_no_se_abre_solo_por_recibir_el_foco():
    codigo = (RUTA_WEB / "js" / "combobox.js").read_text(encoding="utf-8")
    assert 'addEventListener("focus"' not in codigo
    assert 'addEventListener("click"' in codigo
    assert 'addEventListener("input"' in codigo


def test_errores_de_un_campo_se_quitan_al_modificarlo():
    codigo = (RUTA_WEB / "js" / "formulario.js").read_text(encoding="utf-8")
    assert 'addEventListener("input", alModificarCampo)' in codigo
    assert 'addEventListener("change", alModificarCampo)' in codigo
    assert "function quitarErroresDeCampo(nombre)" in codigo


# Textos y parpadeo (ajustes tras la fase 2)

# Textos que son marcas, comandos o rutas y van en minúscula a propósito
CLAVES_EN_MINUSCULA = {
    "marca",
    "idioma.codigo",
    "idioma.boton",
    "formulario.titulo",
    "pie.repositorio",
    "pie.portfolio",
}


def textos_planos(nodo, ruta=""):
    for clave, valor in nodo.items():
        completa = f"{ruta}.{clave}" if ruta else clave
        if isinstance(valor, dict):
            yield from textos_planos(valor, completa)
        else:
            yield completa, valor


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_textos_empiezan_en_mayuscula(idioma):
    diccionario = json.loads((RUTA_WEB / "i18n" / f"{idioma}.json").read_text(encoding="utf-8"))
    for clave, texto in textos_planos(diccionario):
        # Los que empiezan por un dato ("{tramo}: error relativo...") siguen tras los dos puntos
        if clave in CLAVES_EN_MINUSCULA or texto.startswith("{"):
            continue
        letras = re.sub(r"^(> |ERROR: |-- |\[ ?)", "", texto)
        primera = re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", letras)
        assert primera is None or not primera.group(0).islower(), f"{idioma}: {clave}"


def test_unico_parpadeo_es_el_de_la_linea_lista():
    css = (RUTA_WEB / "css" / "estilo.css").read_text(encoding="utf-8")
    sin_comentarios = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    bloques = re.findall(r"([^{}]+)\{[^{}]*animation:\s*parpadeo", sin_comentarios)
    assert [bloque.strip() for bloque in bloques] == [".registro .linea-lista::after"]
    assert 'class="cursor"' not in (RUTA_WEB / "index.html").read_text(encoding="utf-8")


def test_grupo_legal_se_llama_situacion_legal():
    grupos = {}
    for grupo in construir_metadata().option_groups:
        grupos[grupo.key] = grupo.label
    assert grupos["legal_and_listing"].es == "Situación legal"
    assert grupos["legal_and_listing"].en == "Legal status"


def test_holograma_traducido_y_conectado_al_calculo():
    for idioma in ("es", "en"):
        diccionario = json.loads((RUTA_WEB / "i18n" / f"{idioma}.json").read_text(encoding="utf-8"))
        assert set(diccionario["holograma"]) == {"cabecera", "salida"}
    app = (RUTA_WEB / "js" / "app.js").read_text(encoding="utf-8")
    assert "activarHolograma();" in app
