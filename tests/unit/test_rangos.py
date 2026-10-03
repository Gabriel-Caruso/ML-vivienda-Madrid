"""Tests de los rangos válidos."""

import pytest

from tasador.domain.rangos import RANGO_BANOS, RANGO_HABITACIONES, RANGO_METROS, Rango


def test_rangos_aprobados():
    assert RANGO_METROS == Rango(minimo=10, maximo=3100)
    assert RANGO_HABITACIONES == Rango(minimo=0, maximo=20)
    assert RANGO_BANOS == Rango(minimo=1, maximo=7)


@pytest.mark.parametrize(
    ("valor", "esperado"), [(9, False), (10, True), (3100, True), (3101, False)]
)
def test_limites_de_metros_son_cerrados(valor, esperado):
    assert RANGO_METROS.contiene(valor) is esperado


def test_cero_banos_fuera_de_rango():
    assert not RANGO_BANOS.contiene(0)


def test_cero_habitaciones_dentro_de_rango():
    assert RANGO_HABITACIONES.contiene(0)


def test_rangos_cubren_lo_visto_en_entrenamiento():
    # Mínimos y máximos de data/train.csv: metros 11-3015, habitaciones 0-20, baños 1-7
    assert RANGO_METROS.contiene(11)
    assert RANGO_METROS.contiene(3015)
    assert RANGO_HABITACIONES.contiene(20)
    assert RANGO_BANOS.contiene(1)
    assert RANGO_BANOS.contiene(7)
