"""Tests de validación del contrato de entrada, campo a campo."""

import pytest
from pydantic import ValidationError

from tasador.domain.campos import CAMPOS
from tasador.schemas.prediccion import PeticionPrediccion
from tests.ayudas import peticion_valida


def codigos_de_error(datos: dict) -> list[tuple[str, tuple]]:
    """Valida y devuelve (tipo, ubicación) de cada error."""
    with pytest.raises(ValidationError) as informacion:
        PeticionPrediccion.model_validate(datos)
    resultado = []
    for error in informacion.value.errors():
        resultado.append((error["type"], error["loc"]))
    return resultado


def con(**cambios) -> dict:
    datos = peticion_valida()
    datos.update(cambios)
    return datos


def sin(campo: str) -> dict:
    datos = peticion_valida()
    del datos[campo]
    return datos


def test_peticion_valida():
    peticion = PeticionPrediccion.model_validate(peticion_valida())
    assert peticion.area_m2 == 85
    assert peticion.options == ["terrace", "renovated"]


def test_campos_del_esquema_son_los_del_dominio():
    nombres_dominio = []
    for campo in CAMPOS:
        nombres_dominio.append(campo.nombre)
    assert set(PeticionPrediccion.model_fields) == {*nombres_dominio, "options"}


def test_peticion_minima_rellena_opcionales_con_null_y_sin_opciones():
    peticion = PeticionPrediccion.model_validate(
        {
            "area_m2": 60,
            "district": "centro",
            "neighbourhood": "Sol",
            "property_type": "Piso",
        }
    )
    assert peticion.bathrooms is None
    assert peticion.rooms is None
    assert peticion.lift is None
    assert peticion.position is None
    assert peticion.floor is None
    assert peticion.options == []


# Obligatorios, desconocidos y tipos


@pytest.mark.parametrize("campo", ["area_m2", "district", "neighbourhood", "property_type"])
def test_campo_obligatorio(campo):
    assert codigos_de_error(sin(campo)) == [("missing", (campo,))]


def test_campo_desconocido_rechazado():
    assert codigos_de_error(con(precio=1)) == [("extra_forbidden", ("precio",))]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("area_m2", "85"),
        ("area_m2", 85.5),
        ("area_m2", True),
        ("bathrooms", "2"),
        ("rooms", 2.0),
        ("district", 3),
        ("options", "terrace"),
    ],
)
def test_tipos_estrictos(campo, valor):
    tipo, ubicacion = codigos_de_error(con(**{campo: valor}))[0]
    assert ubicacion[0] == campo
    assert tipo.endswith("_type")


# Rangos


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("area_m2", 9), ("area_m2", 3101), ("rooms", -1), ("rooms", 21), ("bathrooms", 8)],
)
def test_fuera_de_rango(campo, valor):
    assert codigos_de_error(con(**{campo: valor})) == [("OUT_OF_RANGE", (campo,))]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("area_m2", 10), ("area_m2", 3100), ("rooms", 0), ("rooms", 20), ("bathrooms", 1)],
)
def test_limites_de_rango_validos(campo, valor):
    PeticionPrediccion.model_validate(con(**{campo: valor}))


def test_banos_cero_tiene_codigo_propio():
    assert codigos_de_error(con(bathrooms=0)) == [("BATHROOMS_ZERO", ("bathrooms",))]


def test_banos_negativo_es_fuera_de_rango():
    assert codigos_de_error(con(bathrooms=-1)) == [("OUT_OF_RANGE", ("bathrooms",))]


@pytest.mark.parametrize("campo", ["bathrooms", "rooms", "lift", "position", "floor"])
def test_opcionales_admiten_null(campo):
    peticion = PeticionPrediccion.model_validate(con(**{campo: None}))
    assert getattr(peticion, campo) is None


# Catálogo


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("district", "san-sebastian-de-los-reyes"),
        ("district", "Centro"),
        ("neighbourhood", "Barrio inventado"),
        ("property_type", "Loft"),
        ("lift", "SI"),
        ("lift", "DESCONOCIDO"),
        ("position", "NO_APLICA"),
        ("floor", "22ª"),
        ("floor", "DESCONOCIDO"),
    ],
)
def test_valor_fuera_de_catalogo(campo, valor):
    assert codigos_de_error(con(**{campo: valor})) == [("VALUE_NOT_IN_CATALOG", (campo,))]


def test_barrio_de_otra_zona():
    errores = codigos_de_error(con(district="centro", neighbourhood="Sanchinarro"))
    assert errores == [("BARRIO_NOT_IN_ZONE", ())]


def test_barrio_no_se_compara_si_la_zona_ya_es_invalida():
    errores = codigos_de_error(con(district="zona-inventada", neighbourhood="Sanchinarro"))
    assert errores == [("VALUE_NOT_IN_CATALOG", ("district",))]


# Opciones


def test_opcion_desconocida():
    assert codigos_de_error(con(options=["terrace", "jacuzzi"])) == [
        ("UNKNOWN_OPTION", ("options",))
    ]


def test_tag_no_publico_no_es_opcion():
    assert codigos_de_error(con(options=["tag_piso"])) == [("UNKNOWN_OPTION", ("options",))]


def test_varios_errores_a_la_vez():
    errores = codigos_de_error(con(area_m2=5, bathrooms=0, floor="99ª"))
    tipos = set()
    for tipo, _ in errores:
        tipos.add(tipo)
    assert tipos == {"OUT_OF_RANGE", "BATHROOMS_ZERO", "VALUE_NOT_IN_CATALOG"}
