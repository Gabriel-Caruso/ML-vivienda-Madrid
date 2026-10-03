"""Tests de las reglas del preprocesado original."""

import pytest

from tasador.domain.reglas import (
    TIPOS_CASA_O_CHALET,
    VALOR_DESCONOCIDO,
    VALOR_NO_APLICA,
    completar_habitaciones,
    valor_sin_dato,
)


@pytest.mark.parametrize("tipo", sorted(TIPOS_CASA_O_CHALET))
def test_casas_y_chalets_sin_dato_son_no_aplica(tipo):
    assert valor_sin_dato(tipo) == VALOR_NO_APLICA


@pytest.mark.parametrize("tipo", ["Piso", "Ático", "Dúplex", "Estudio"])
def test_resto_de_tipos_sin_dato_son_desconocido(tipo):
    assert valor_sin_dato(tipo) == VALOR_DESCONOCIDO


def test_casas_y_chalets_son_los_cinco_del_notebook():
    assert {
        "Casa o chalet independiente",
        "Chalet adosado",
        "Chalet pareado",
        "Chalet",
        "Casa rural",
    } == TIPOS_CASA_O_CHALET


def test_estudio_sin_habitaciones_pasa_a_cero():
    assert completar_habitaciones("Estudio", None) == 0


def test_estudio_con_habitaciones_las_conserva():
    assert completar_habitaciones("Estudio", 1) == 1


def test_otro_tipo_sin_habitaciones_sigue_desconocido():
    assert completar_habitaciones("Piso", None) is None


def test_cero_habitaciones_es_valido_en_cualquier_tipo():
    assert completar_habitaciones("Piso", 0) == 0
