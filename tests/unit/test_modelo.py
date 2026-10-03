"""Tests del modelo serializado: carga, estructura y capacidad de predecir.

No evalúan el rendimiento del modelo: solo comprueban que el archivo es el
esperado y que funciona en este entorno.
"""

import warnings

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.compose import TransformedTargetRegressor

from tasador.config import RUTA_MODELO

NUMERICAS = ["metros", "baños_limpio", "habitaciones_limpio"]
CATEGORICAS = [
    "zona",
    "tipo_inmueble",
    "ascensor_limpio",
    "localizacion_limpio",
    "barrio",
    "planta_limpio",
]
FLAGS = [
    "flag_rebaja",
    "flag_loft",
    "flag_nuda_propiedad",
    "flag_proindiviso",
    "flag_subasta",
    "flag_okupada",
    "flag_alquilada",
]
NUMERO_TAGS = 53

# Valores tomados de la primera fila de data/test.csv
FILA_EJEMPLO = {
    "metros": 266,
    "baños_limpio": np.nan,
    "habitaciones_limpio": 3.0,
    "zona": "chamartin",
    "tipo_inmueble": "Ático",
    "ascensor_limpio": "S",
    "localizacion_limpio": "EXTERIOR",
    "barrio": "Prosperidad",
    "planta_limpio": "12ª",
}


def construir_fila(columnas_modelo):
    """Fila con los valores de ejemplo y todos los flags y tags a 0."""
    fila = {}
    for columna in columnas_modelo:
        fila[columna] = FILA_EJEMPLO.get(columna, 0)
    return pd.DataFrame([fila], columns=columnas_modelo)


def test_modelo_carga_sin_avisos():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        joblib.load(RUTA_MODELO)
    assert [str(aviso.message) for aviso in avisos] == []


def test_modelo_es_catboost_con_objetivo_logaritmico(modelo):
    assert isinstance(modelo, TransformedTargetRegressor)
    assert isinstance(modelo.regressor_, CatBoostRegressor)
    assert modelo.func is np.log1p
    assert modelo.inverse_func is np.expm1


def test_modelo_tiene_69_columnas(modelo):
    assert len(modelo.regressor_.feature_names_) == 69


def test_columnas_numericas_categoricas_y_flags_en_su_posicion(modelo):
    columnas = list(modelo.regressor_.feature_names_)
    assert columnas[:9] == NUMERICAS + CATEGORICAS
    assert columnas[9:16] == FLAGS


def test_resto_de_columnas_son_tags(modelo):
    columnas_tag = list(modelo.regressor_.feature_names_)[16:]
    assert len(columnas_tag) == NUMERO_TAGS
    for columna in columnas_tag:
        assert columna.startswith("tag_")


def test_categoricas_nativas_son_las_esperadas(modelo):
    columnas = modelo.regressor_.feature_names_
    indices = modelo.regressor_.get_cat_feature_indices()
    categoricas_modelo = []
    for indice in indices:
        categoricas_modelo.append(columnas[indice])
    assert categoricas_modelo == CATEGORICAS


def test_modelo_predice_un_valor_finito(modelo):
    fila = construir_fila(list(modelo.regressor_.feature_names_))
    prediccion = modelo.predict(fila)
    assert prediccion.shape == (1,)
    assert np.isfinite(prediccion[0])
