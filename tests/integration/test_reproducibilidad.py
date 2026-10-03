"""Los archivos versionados coinciden con lo que generan los scripts desde data/.

Solo se ejecutan si existen los CSV locales (no están en el repositorio ni en
la CI). Detectan un catálogo o unos fixtures desactualizados o editados a mano.
"""

import json

import build_catalog
import build_fixtures
import pandas as pd
import pytest
from preprocesado_original import (
    RUTA_TEST,
    RUTA_TRAIN,
    anadir_columnas_tag,
    calcular_etiquetas_utiles,
)

from tasador.config import RUTA_CATALOGO

sin_datos = pytest.mark.skipif(
    not (RUTA_TRAIN.is_file() and RUTA_TEST.is_file()),
    reason="data/train.csv y data/test.csv solo existen en local",
)


@sin_datos
def test_catalogo_versionado_coincide_con_el_generado():
    train = pd.read_csv(RUTA_TRAIN)
    catalogo = build_catalog.construir_catalogo(train, build_catalog.calcular_sha256(RUTA_TRAIN))
    generado = build_catalog.serializar_catalogo(catalogo)
    assert RUTA_CATALOGO.read_text(encoding="utf-8") == generado


@sin_datos
def test_fixtures_versionados_coinciden_con_los_generados(modelo, catalogo):
    columnas_modelo = list(modelo.regressor_.feature_names_)
    columnas_binarias = []
    for columna in columnas_modelo:
        if columna.startswith(("flag_", "tag_")):
            columnas_binarias.append(columna)

    test = anadir_columnas_tag(
        pd.read_csv(RUTA_TEST), calcular_etiquetas_utiles(pd.read_csv(RUTA_TRAIN))
    )
    expresables = []
    for indice, fila in test.iterrows():
        if build_fixtures.es_expresable(fila, columnas_binarias, catalogo):
            expresables.append(indice)
    candidatas = test.loc[expresables]
    seleccion = build_fixtures.seleccionar_filas(
        candidatas, build_fixtures.NUMERO_FILAS, build_fixtures.SEMILLA
    )
    generado = build_fixtures.construir_fixture(candidatas.loc[seleccion], columnas_modelo)

    versionado = json.loads(build_fixtures.RUTA_FIXTURES.read_text(encoding="utf-8"))
    assert versionado == generado


@sin_datos
def test_filas_del_fixture_son_identicas_a_las_del_notebook(filas_referencia):
    test = anadir_columnas_tag(
        pd.read_csv(RUTA_TEST), calcular_etiquetas_utiles(pd.read_csv(RUTA_TRAIN))
    )
    for fila in filas_referencia["filas"]:
        original = test.loc[fila["indice_test"]]
        for columna, valor in fila["valores"].items():
            if valor is None:
                assert pd.isna(original[columna]), f"{fila['indice_test']} {columna}"
            else:
                assert original[columna] == valor, f"{fila['indice_test']} {columna}"
