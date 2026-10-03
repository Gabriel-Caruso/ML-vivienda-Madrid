"""Tests del cálculo de la horquilla por tramos."""

import pytest

from tasador.config import TRAMOS_ERROR
from tasador.services.horquilla import calcular_horquilla, comprobar_tramos, margen_para


def test_tramos_configurados_son_los_del_readme():
    assert TRAMOS_ERROR == (
        (0, 0.16),
        (250_000, 0.15),
        (435_360, 0.16),
        (835_600, 0.15),
        (1_490_000, 0.24),
    )


@pytest.mark.parametrize(
    ("precio", "margen"),
    [
        (188_604, 0.16),
        (335_000, 0.15),
        (599_900, 0.16),
        (1_150_000, 0.15),
        (2_350_000, 0.24),
    ],
)
def test_margen_en_cada_tramo(precio, margen):
    assert margen_para(precio) == margen


@pytest.mark.parametrize(
    ("precio", "margen"),
    [
        (249_999.99, 0.16),
        (250_000, 0.15),
        (435_360, 0.16),
        (835_600, 0.15),
        (1_489_999.99, 0.15),
        (1_490_000, 0.24),
    ],
)
def test_limite_pertenece_al_tramo_superior(precio, margen):
    assert margen_para(precio) == margen


def test_precio_por_debajo_de_la_tabla_usa_el_primer_tramo():
    assert margen_para(20_000) == 0.16


def test_precio_por_encima_de_la_tabla_usa_el_ultimo_tramo():
    assert margen_para(20_000_000) == 0.24


def test_horquilla_tramo_general():
    horquilla = calcular_horquilla(300_000)
    assert horquilla.margen == 0.15
    assert horquilla.minimo == pytest.approx(255_000)
    assert horquilla.maximo == pytest.approx(345_000)


def test_horquilla_tramo_lujo():
    horquilla = calcular_horquilla(2_000_000)
    assert horquilla.margen == 0.24
    assert horquilla.minimo == pytest.approx(1_520_000)
    assert horquilla.maximo == pytest.approx(2_480_000)


def test_horquilla_con_tramos_propios():
    horquilla = calcular_horquilla(100, tramos=((0, 0.1),))
    assert horquilla.minimo == pytest.approx(90)
    assert horquilla.maximo == pytest.approx(110)


@pytest.mark.parametrize(
    "tramos",
    [
        (),
        ((100, 0.1),),
        ((0, 0.1), (500, 0.2), (300, 0.1)),
        ((0, 0.1), (500, 0.1), (500, 0.2)),
        ((0, 0.0),),
        ((0, 1.5),),
    ],
)
def test_tramos_mal_definidos_se_rechazan(tramos):
    with pytest.raises(ValueError):
        comprobar_tramos(tramos)
