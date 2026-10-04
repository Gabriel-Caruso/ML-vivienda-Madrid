"""Tests de las funciones puras de los scripts de datos de la web."""

import numpy as np
import pandas as pd
import pytest
from build_model_report import (
    InformeIncoherenteError,
    calcular_metricas,
    calcular_tramos,
    comprobar_coherencia_con_api,
    comprobar_metricas,
    etiqueta_variable,
    puntos_real_predicho,
)
from export_tree import (
    ArbolIncoherenteError,
    comprobar_ramas,
    describir_corte,
    etiquetas_por_nivel,
    ramas_desde_hoja,
)
from salida_json import serializar

# salida_json


def test_serializacion_estable_y_en_utf8():
    datos = {"barrio": "Águilas", "valor": 1.5}
    assert serializar(datos) == serializar(datos)
    assert "Águilas" in serializar(datos)
    assert serializar(datos).endswith("\n")


# build_model_report


def test_metricas_de_un_caso_conocido():
    reales = np.array([100.0, 200.0, 300.0])
    predichos = np.array([110.0, 190.0, 300.0])
    metricas = calcular_metricas(reales, predichos)
    assert metricas["mae"] == pytest.approx(6.67)
    assert metricas["rmse"] == pytest.approx(8.16)


def test_metricas_distintas_de_las_documentadas_fallan():
    with pytest.raises(InformeIncoherenteError, match="mae"):
        comprobar_metricas({"mae": 1.0, "rmse": 439_764.62, "r2": 0.8635})


def test_metricas_documentadas_pasan():
    comprobar_metricas({"mae": 180_709.77, "rmse": 439_764.62, "r2": 0.8635})


def test_tramos_por_quintiles_con_error_relativo():
    reales = np.array([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
    predichos = reales * 1.1
    tramos = calcular_tramos(reales, predichos)
    assert len(tramos) == 5
    for tramo in tramos:
        assert tramo["viviendas"] == 2
    # Primer tramo: reales 10 y 20, errores 1 y 2: MAE 1.5, mediana 15
    assert tramos[0]["mae"] == 2
    assert tramos[0]["precio_mediano"] == 15
    assert tramos[0]["error_relativo"] == 0.1


def tramos_sinteticos(errores):
    limites = (35_000, 250_000, 435_360, 835_600, 1_490_000, 13_000_000)
    tramos = []
    for posicion, error in enumerate(errores):
        tramos.append(
            {
                "limite_inferior": limites[posicion],
                "limite_superior": limites[posicion + 1],
                "error_relativo": error,
            }
        )
    return tramos


def test_tramos_coherentes_con_la_api_pasan():
    comprobar_coherencia_con_api(tramos_sinteticos([0.167, 0.1478, 0.1553, 0.1548, 0.236]))


def test_tramo_con_margen_distinto_de_la_api_falla():
    with pytest.raises(InformeIncoherenteError, match="Tramo 0"):
        comprobar_coherencia_con_api(tramos_sinteticos([0.164, 0.1478, 0.1553, 0.1548, 0.236]))


def test_tramo_con_corte_distinto_de_la_api_falla():
    tramos = tramos_sinteticos([0.167, 0.1478, 0.1553, 0.1548, 0.236])
    tramos[1]["limite_inferior"] = 260_000
    with pytest.raises(InformeIncoherenteError, match="corte"):
        comprobar_coherencia_con_api(tramos)


def test_puntos_ordenados_por_precio_real_y_en_enteros():
    puntos = puntos_real_predicho(np.array([300.4, 100.6, 200.0]), np.array([290.0, 110.2, 205.7]))
    assert puntos == {"reales": [101, 200, 300], "predichos": [110, 206, 290]}


def test_etiqueta_de_campo_principal_y_de_binaria():
    assert etiqueta_variable("baños_limpio") == {"es": "Baños", "en": "Bathrooms"}
    assert etiqueta_variable("tag_finca") == {"es": "tag_finca", "en": "tag_finca"}


# export_tree


@pytest.mark.parametrize(
    ("etiqueta", "esperado"),
    [
        (
            "metros, value>69.5",
            {"variable": "metros", "tipo": "numerica", "umbral": 69.5, "texto": "metros > 69.5"},
        ),
        (
            "tag_finca, value>0.5",
            {"variable": "tag_finca", "tipo": "binaria", "umbral": 0.5, "texto": "tag_finca > 0.5"},
        ),
        (
            "{zona} counter_type=Borders prior_numerator=0, value>3",
            {"variable": "zona", "tipo": "ctr", "umbral": 3.0, "texto": "ctr(zona) > 3"},
        ),
        (
            "{ascensor_limpio} counter_type=Counter prior_numerator=0.5, value>8",
            {
                "variable": "ascensor_limpio",
                "tipo": "ctr",
                "umbral": 8.0,
                "texto": "ctr(ascensor) > 8",
            },
        ),
    ],
)
def test_describir_corte(etiqueta, esperado):
    assert describir_corte(etiqueta) == esperado


def test_corte_con_formato_desconocido_falla():
    with pytest.raises(ArbolIncoherenteError):
        describir_corte("zona == centro")


def test_etiquetas_por_nivel_sigue_la_raiz_hacia_abajo():
    fuente = """digraph {
        0 [label="a, value>1"]
        1 [label="b, value>2"]
        2 [label="b, value>2"]
        3 [label="val = 1"]
        4 [label="val = 2"]
        5 [label="val = 3"]
        6 [label="val = 4"]
        0 -> 1 [label=No]
        0 -> 2 [label=Yes]
        1 -> 3 [label=No]
        1 -> 4 [label=Yes]
        2 -> 5 [label=No]
        2 -> 6 [label=Yes]
    }"""
    assert etiquetas_por_nivel(fuente) == ["a, value>1", "b, value>2"]


@pytest.mark.parametrize(
    ("hoja", "ramas"),
    [(0, [0, 0, 0]), (1, [0, 0, 1]), (4, [1, 0, 0]), (6, [1, 1, 0]), (7, [1, 1, 1])],
)
def test_ramas_desde_hoja_el_primer_nivel_es_el_bit_mas_alto(hoja, ramas):
    assert ramas_desde_hoja(hoja, 3) == ramas


def test_comprobar_ramas_detecta_un_orden_de_bits_equivocado():
    niveles = [
        {"variable": "metros", "tipo": "numerica", "umbral": 100.0},
        {"variable": "zona", "tipo": "ctr", "umbral": 3.0},
    ]
    filas = pd.DataFrame({"metros": [150, 50], "zona": ["centro", "latina"]})
    comprobar_ramas(niveles, filas, [[1, 0], [0, 1]])
    with pytest.raises(ArbolIncoherenteError):
        comprobar_ramas(niveles, filas, [[0, 1], [1, 0]])


def test_comprobar_ramas_trata_nan_como_condicion_falsa():
    niveles = [{"variable": "baños_limpio", "tipo": "numerica", "umbral": 1.5}]
    filas = pd.DataFrame({"baños_limpio": [np.nan]})
    comprobar_ramas(niveles, filas, [[0]])
