"""Tests de los JSON estáticos de la web: estructura, coherencia y determinismo.

Solo usan lo versionado (modelo, fixtures y los propios JSON), así que se
ejecutan también en la CI.
"""

import json

import build_web_catalog
import export_tree
from salida_json import serializar

from tasador.config import RUTA_DATOS_WEB, TRAMOS_ERROR


def leer(nombre: str) -> dict:
    return json.loads((RUTA_DATOS_WEB / nombre).read_text(encoding="utf-8"))


# Catálogo


def test_catalogo_estatico_identico_a_metadata_de_la_api(cliente):
    respuesta = cliente.get("/api/v1/metadata")
    assert respuesta.status_code == 200
    assert leer("catalogo.json") == respuesta.json()


def test_catalogo_estatico_al_dia_con_el_dominio():
    texto = (RUTA_DATOS_WEB / "catalogo.json").read_text(encoding="utf-8")
    assert texto == serializar(build_web_catalog.construir_catalogo_web())


# Informe del modelo


def test_informe_tiene_las_secciones_que_espera_la_web():
    informe = leer("informe_modelo.json")
    assert set(informe) == {
        "modelo",
        "metricas_test",
        "error_por_tramo",
        "real_frente_a_predicho",
        "importancia_variables",
        "mae_por_modelo",
    }


def test_metricas_son_las_documentadas():
    metricas = leer("informe_modelo.json")["metricas_test"]
    assert metricas["mae"] == 180_709.77
    assert metricas["rmse"] == 439_764.62
    assert round(metricas["r2"], 4) == 0.8635
    # Con tres decimales, como en el README (sin doble redondeo: 0,8635 daría 0,864)
    assert round(metricas["r2"], 3) == 0.863


def test_datos_del_modelo():
    modelo = leer("informe_modelo.json")["modelo"]
    assert modelo["biblioteca"] == "catboost"
    assert modelo["version"] == "1.2.10"
    assert modelo["arboles"] == 2044
    assert modelo["profundidad"] == 9
    assert modelo["variables"] == 69
    assert modelo["datos"] == "Idealista Madrid 2025"


def test_tramos_coherentes_con_la_horquilla_de_la_api():
    tramos = leer("informe_modelo.json")["error_por_tramo"]
    assert len(tramos) == len(TRAMOS_ERROR)
    for posicion, tramo in enumerate(tramos):
        limite_api, margen_api = TRAMOS_ERROR[posicion]
        assert set(tramo) == {
            "limite_inferior",
            "limite_superior",
            "viviendas",
            "precio_mediano",
            "mae",
            "error_relativo",
        }
        if posicion > 0:
            assert tramo["limite_inferior"] == limite_api
            assert tramo["limite_inferior"] == tramos[posicion - 1]["limite_superior"]
        assert round(tramo["error_relativo"], 2) == margen_api
        assert tramo["limite_inferior"] < tramo["precio_mediano"] <= tramo["limite_superior"]


def test_tramos_cubren_todo_test():
    informe = leer("informe_modelo.json")
    total = 0
    for tramo in informe["error_por_tramo"]:
        total += tramo["viviendas"]
    assert total == informe["modelo"]["viviendas_test"] == 2237


def test_puntos_real_frente_a_predicho():
    puntos = leer("informe_modelo.json")["real_frente_a_predicho"]
    assert len(puntos["reales"]) == len(puntos["predichos"]) == 2237
    for valor in puntos["reales"] + puntos["predichos"]:
        assert isinstance(valor, int)
        assert valor > 0
    assert puntos["reales"] == sorted(puntos["reales"])


def test_importancias_ordenadas_y_con_etiqueta():
    importancias = leer("informe_modelo.json")["importancia_variables"]
    assert len(importancias) == 69
    assert [variable["columna"] for variable in importancias[:3]] == ["metros", "zona", "barrio"]
    assert importancias[0]["importancia"] == 41.675
    assert importancias[0]["etiqueta"] == {"es": "Metros cuadrados", "en": "Square metres"}
    total = 0
    for posicion, variable in enumerate(importancias):
        assert set(variable) == {"columna", "etiqueta", "importancia"}
        total += variable["importancia"]
        if posicion > 0:
            assert variable["importancia"] <= importancias[posicion - 1]["importancia"]
    assert round(total) == 100


def test_serie_mae_por_modelo():
    serie = leer("informe_modelo.json")["mae_por_modelo"]
    assert len(serie) == 8
    assert serie[0]["modelo"]["es"] == "Regresión lineal"
    assert serie[0]["mae"] == 356_861
    for punto in serie[:-1]:
        assert punto["conjunto"] == "cv"
    assert serie[-1]["conjunto"] == "test"
    assert serie[-1]["mae"] == round(leer("informe_modelo.json")["metricas_test"]["mae"])
    for punto in serie:
        assert set(punto) == {"modelo", "mae", "conjunto", "origen"}
        assert punto["origen"].startswith("modeling.ipynb, celda ")


# Árbol


def test_arbol_tiene_la_estructura_que_espera_la_web():
    arbol = leer("arbol.json")
    assert arbol["arbol"] == 0
    assert arbol["profundidad"] == 9
    assert arbol["hojas"] == 512
    assert len(arbol["niveles"]) == 9
    for corte in arbol["niveles"]:
        assert set(corte) == {"variable", "tipo", "umbral", "texto"}
        assert corte["tipo"] in {"numerica", "binaria", "ctr"}
        assert " > " in corte["texto"]
    assert arbol["niveles"][0]["texto"] == "tag_finca > 0.5"


def test_recorridos_de_las_viviendas_de_referencia(filas_referencia):
    arbol = leer("arbol.json")
    assert len(arbol["recorridos"]) == len(filas_referencia["filas"])
    for recorrido in arbol["recorridos"]:
        assert len(recorrido["ramas"]) == 9
        assert set(recorrido["ramas"]) <= {0, 1}


def test_arbol_estatico_al_dia_y_determinista(modelo):
    filas, indices = export_tree.cargar_filas_referencia()
    primero = serializar(export_tree.construir_arbol(modelo, filas, indices))
    segundo = serializar(export_tree.construir_arbol(modelo, filas, indices))
    assert primero == segundo
    assert (RUTA_DATOS_WEB / "arbol.json").read_text(encoding="utf-8") == primero
