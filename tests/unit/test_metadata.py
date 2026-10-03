"""Tests de la metadata del formulario."""

from tasador.domain.catalogo import clave_orden_alfabetico
from tasador.domain.reglas import VALORES_SIN_DATO
from tasador.services.metadata import construir_metadata


def test_campos_con_etiqueta_obligatoriedad_y_rango():
    campos = {}
    for campo in construir_metadata().fields:
        campos[campo.name] = campo
    assert campos["bathrooms"].label.es == "Baños"
    assert campos["bathrooms"].label.en == "Bathrooms"
    assert campos["bathrooms"].required is False
    assert (campos["bathrooms"].range.min, campos["bathrooms"].range.max) == (1, 7)
    assert campos["area_m2"].required is True
    assert (campos["area_m2"].range.min, campos["area_m2"].range.max) == (10, 3100)
    assert campos["district"].range is None


def test_distritos_con_nombre_oficial_y_sus_barrios(catalogo):
    distritos = construir_metadata().districts
    assert len(distritos) == 21
    for distrito in distritos:
        assert distrito.neighbourhoods == list(catalogo.barrios_por_zona[distrito.value])
        assert distrito.label.es == distrito.label.en
    nombres = {}
    for distrito in distritos:
        nombres[distrito.value] = distrito.label.es
    assert nombres["fuencarral"] == "Fuencarral-El Pardo"
    assert nombres["barrio-de-salamanca"] == "Salamanca"


def test_distritos_ordenados_por_nombre_visible():
    nombres = []
    for distrito in construir_metadata().districts:
        nombres.append(distrito.label.es)
    assert nombres == sorted(nombres, key=clave_orden_alfabetico)


def test_valores_sin_dato_no_se_ofrecen():
    metadata = construir_metadata()
    for opciones in (metadata.lift, metadata.position, metadata.floors):
        for opcion in opciones:
            assert opcion.value not in VALORES_SIN_DATO


def test_tipos_de_inmueble_traducidos():
    etiquetas = {}
    for opcion in construir_metadata().property_types:
        etiquetas[opcion.value] = opcion.label
    assert len(etiquetas) == 9
    assert etiquetas["Piso"].en == "Flat"
    assert etiquetas["Ático"].en == "Penthouse"


def test_plantas_en_orden_y_con_etiqueta():
    plantas = construir_metadata().floors
    assert plantas[0].value == "-2"
    assert plantas[2].label.en == "Ground floor"


def test_grupos_de_opciones():
    grupos = construir_metadata().option_groups
    numero_por_grupo = {}
    for grupo in grupos:
        numero_por_grupo[grupo.key] = len(grupo.options)
    assert numero_por_grupo == {"property_features": 22, "legal_and_listing": 9}
    assert grupos[0].label.es == "Características de la vivienda"
