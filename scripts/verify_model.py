"""Comprueba que el modelo carga y predice en el entorno actual.

1. Carga models/catboost_madrid.joblib registrando cualquier aviso.
2. Reconstruye las filas de data/test.csv como en el notebook y predice la primera.
3. Si existe data/catboost_madrid.pkl, compara sus predicciones con las del
   joblib sobre todo test.csv. Solo comprueba que son idénticas: no calcula
   métricas ni usa el precio real.

Uso: uv run python scripts/verify_model.py
"""

import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from preprocesado_original import (
    RUTA_MODELO,
    RUTA_MODELO_PKL,
    RUTA_TEST,
    RUTA_TRAIN,
    anadir_columnas_tag,
    calcular_etiquetas_utiles,
)


def cargar_modelo_vigilando_avisos(ruta: Path):
    """Carga un modelo con joblib y devuelve el modelo y los avisos emitidos."""
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        modelo = joblib.load(ruta)
    return modelo, [str(aviso.message) for aviso in avisos]


def main() -> int:
    modelo, avisos = cargar_modelo_vigilando_avisos(RUTA_MODELO)
    print(f"Modelo cargado: {type(modelo).__name__} -> {type(modelo.regressor_).__name__}")
    print(f"Avisos al cargar el joblib: {avisos if avisos else 'ninguno'}")

    columnas_modelo = list(modelo.regressor_.feature_names_)
    etiquetas = calcular_etiquetas_utiles(pd.read_csv(RUTA_TRAIN))
    test = anadir_columnas_tag(pd.read_csv(RUTA_TEST), etiquetas)

    faltan = []
    for columna in columnas_modelo:
        if columna not in test.columns:
            faltan.append(columna)
    if faltan:
        print(f"ERROR: faltan columnas del modelo en test: {faltan}")
        return 1

    x_test = test[columnas_modelo]

    with warnings.catch_warnings(record=True) as avisos_prediccion:
        warnings.simplefilter("always")
        prediccion = modelo.predict(x_test.iloc[[0]])
    print(f"Avisos al predecir: {[str(a.message) for a in avisos_prediccion] or 'ninguno'}")
    print(f"Predicción sobre la primera fila de test: {prediccion[0]:.2f} EUR")
    if not np.isfinite(prediccion).all():
        print("ERROR: la predicción no es un número finito")
        return 1

    if not RUTA_MODELO_PKL.is_file():
        print("No existe data/catboost_madrid.pkl: se omite la comparación.")
        return 0

    modelo_pkl, avisos_pkl = cargar_modelo_vigilando_avisos(RUTA_MODELO_PKL)
    print(f"Avisos al cargar el pkl: {avisos_pkl if avisos_pkl else 'ninguno'}")

    columnas_pkl = list(modelo_pkl.regressor_.feature_names_)
    if columnas_pkl != columnas_modelo:
        print("El pkl y el joblib NO esperan las mismas columnas: no son el mismo modelo.")
        print(f"  Columnas joblib: {len(columnas_modelo)}  Columnas pkl: {len(columnas_pkl)}")
        solo_pkl = sorted(set(columnas_pkl) - set(columnas_modelo))
        solo_joblib = sorted(set(columnas_modelo) - set(columnas_pkl))
        print(f"  Solo en el pkl: {solo_pkl}")
        print(f"  Solo en el joblib: {solo_joblib}")
        posiciones_distintas = 0
        for posicion in range(min(len(columnas_pkl), len(columnas_modelo))):
            if columnas_pkl[posicion] != columnas_modelo[posicion]:
                posiciones_distintas += 1
        print(f"  Posiciones con distinta columna: {posiciones_distintas}")
        return 1

    pred_joblib = modelo.predict(x_test)
    pred_pkl = modelo_pkl.predict(x_test)
    identicas = np.array_equal(pred_joblib, pred_pkl)
    n_distintas = int((pred_joblib != pred_pkl).sum())
    print(f"Filas comparadas: {len(x_test)}")
    print(f"Predicciones idénticas (bit a bit): {identicas} ({n_distintas} filas distintas)")
    return 0 if identicas else 1


if __name__ == "__main__":
    sys.exit(main())
