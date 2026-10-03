"""Tests de las etiquetas legibles en español e inglés."""

import pytest

from tasador.domain.etiquetas import (
    ETIQUETAS_ASCENSOR,
    ETIQUETAS_LOCALIZACION,
    ETIQUETAS_TIPO_INMUEBLE,
    NOMBRES_ZONA,
    Etiqueta,
    etiqueta_planta,
    sufijo_ordinal_ingles,
)
from tasador.domain.reglas import VALORES_SIN_DATO


def test_todas_las_zonas_del_catalogo_tienen_nombre(catalogo):
    assert set(NOMBRES_ZONA) == set(catalogo.zonas)


def test_todos_los_tipos_del_catalogo_tienen_etiqueta(catalogo):
    assert set(ETIQUETAS_TIPO_INMUEBLE) == set(catalogo.tipos_inmueble)


def test_ascensor_y_localizacion_tienen_etiqueta_salvo_valores_sin_dato(catalogo):
    for valor in catalogo.ascensor:
        assert (valor in ETIQUETAS_ASCENSOR) != (valor in VALORES_SIN_DATO)
    for valor in catalogo.localizacion:
        assert (valor in ETIQUETAS_LOCALIZACION) != (valor in VALORES_SIN_DATO)


def test_todas_las_plantas_del_catalogo_tienen_etiqueta(catalogo):
    for planta in catalogo.plantas:
        if planta not in VALORES_SIN_DATO:
            etiqueta = etiqueta_planta(planta)
            assert etiqueta.es
            assert etiqueta.en


@pytest.mark.parametrize(
    ("planta", "esperada"),
    [
        ("-2", Etiqueta(es="Sótano (-2)", en="Basement (-2)")),
        ("-1", Etiqueta(es="Sótano (-1)", en="Basement (-1)")),
        ("BAJO", Etiqueta(es="Bajo", en="Ground floor")),
        ("ENTREPLANTA", Etiqueta(es="Entreplanta", en="Mezzanine")),
        ("1ª", Etiqueta(es="1ª planta", en="1st floor")),
        ("2ª", Etiqueta(es="2ª planta", en="2nd floor")),
        ("3ª", Etiqueta(es="3ª planta", en="3rd floor")),
        ("12ª", Etiqueta(es="12ª planta", en="12th floor")),
        ("21ª", Etiqueta(es="21ª planta", en="21st floor")),
    ],
)
def test_etiqueta_planta(planta, esperada):
    assert etiqueta_planta(planta) == esperada


@pytest.mark.parametrize("planta", ["3", "PRIMERA", "DESCONOCIDO"])
def test_etiqueta_planta_rechaza_formatos_desconocidos(planta):
    with pytest.raises(ValueError):
        etiqueta_planta(planta)


@pytest.mark.parametrize(
    ("numero", "sufijo"),
    [(1, "st"), (2, "nd"), (3, "rd"), (4, "th"), (11, "th"), (12, "th"), (13, "th"), (22, "nd")],
)
def test_sufijo_ordinal_ingles(numero, sufijo):
    assert sufijo_ordinal_ingles(numero) == sufijo
