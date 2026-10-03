"""Tests de la traducción de errores de Pydantic a códigos estables."""

import pytest

from tasador.api.errores import campo_para, codigo_para, convertir_error
from tasador.schemas.errores import CodigoError


@pytest.mark.parametrize(
    ("tipo", "codigo"),
    [
        ("BARRIO_NOT_IN_ZONE", CodigoError.BARRIO_NOT_IN_ZONE),
        ("BATHROOMS_ZERO", CodigoError.BATHROOMS_ZERO),
        ("missing", CodigoError.FIELD_REQUIRED),
        ("extra_forbidden", CodigoError.UNKNOWN_FIELD),
        ("json_invalid", CodigoError.INVALID_JSON),
        ("int_type", CodigoError.INVALID_TYPE),
        ("string_type", CodigoError.INVALID_TYPE),
        ("int_parsing", CodigoError.INVALID_TYPE),
        ("int_from_float", CodigoError.INVALID_TYPE),
        ("model_attributes_type", CodigoError.INVALID_TYPE),
        ("value_error", CodigoError.INVALID_VALUE),
    ],
)
def test_codigo_para(tipo, codigo):
    assert codigo_para(tipo) == codigo


def test_campo_desde_la_ubicacion():
    assert campo_para(("body", "bathrooms"), {}) == "bathrooms"
    assert campo_para(("body", "options", 2), {}) == "options"
    assert campo_para(("body",), {}) is None


def test_campo_desde_el_contexto_tiene_prioridad():
    assert campo_para(("body",), {"field": "neighbourhood"}) == "neighbourhood"


def test_convertir_error_quita_field_de_los_parametros():
    detalle = convertir_error(
        {
            "type": "BARRIO_NOT_IN_ZONE",
            "loc": ("body",),
            "msg": "mensaje",
            "ctx": {"field": "neighbourhood", "district": "centro"},
        }
    )
    assert detalle.code == CodigoError.BARRIO_NOT_IN_ZONE
    assert detalle.field == "neighbourhood"
    assert detalle.params == {"district": "centro"}


def test_convertir_error_sin_contexto():
    detalle = convertir_error({"type": "missing", "loc": ("body", "area_m2"), "msg": "m"})
    assert detalle.code == CodigoError.FIELD_REQUIRED
    assert detalle.field == "area_m2"
    assert detalle.params == {}


def test_parametros_no_serializables_pasan_a_texto():
    detalle = convertir_error(
        {"type": "value_error", "loc": ("body", "x"), "msg": "m", "ctx": {"error": ValueError("x")}}
    )
    assert detalle.params == {"error": "x"}
