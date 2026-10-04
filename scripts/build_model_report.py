"""Genera los datos de los gráficos de la web a partir del modelo y data/test.csv.

Escribe src/tasador/web/datos/informe_modelo.json con:
- métricas sobre test, comprobadas contra las documentadas en modeling.ipynb;
- gráfico A: error relativo por quintil de precio real, calculado como en
  main.ipynb (celda 96): pd.qcut(precio real, q=5), MAE y precio mediano por
  tramo; el error relativo es MAE del tramo / precio mediano del tramo;
- gráfico B: precio real frente a predicho de cada vivienda de test;
- gráfico C: importancia de variables del modelo final;
- gráfico D: MAE por modelo, copiado de las salidas guardadas de
  modeling.ipynb (no se recalcula: requeriría reentrenar).

Solo carga el modelo y predice; no lo modifica ni lo guarda. Es determinista.
Si las métricas no coinciden con las documentadas, o los tramos no coinciden
con los de la horquilla de la API, falla sin escribir nada.

Uso: uv run python scripts/build_model_report.py
"""

import sys

import catboost
import joblib
import numpy as np
import pandas as pd
from preprocesado_original import (
    RUTA_MODELO,
    RUTA_TEST,
    RUTA_TRAIN,
    anadir_columnas_tag,
    calcular_etiquetas_utiles,
)
from salida_json import escribir
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from tasador.config import RUTA_DATOS_WEB, TRAMOS_ERROR
from tasador.domain.campos import CAMPOS

RUTA_INFORME = RUTA_DATOS_WEB / "informe_modelo.json"

# Salida guardada de modeling.ipynb, celda 36 (modelo final contra test)
# Se comparan con la precisión con que están documentadas; el informe guarda el
# R² con más decimales para que la web lo pueda redondear sin redondear dos veces.
METRICAS_DOCUMENTADAS = {"mae": 180_709.77, "rmse": 439_764.62, "r2": 0.8635}
DECIMALES_DOCUMENTADOS = {"mae": 2, "rmse": 2, "r2": 4}
DECIMALES_METRICAS = {"mae": 2, "rmse": 2, "r2": 6}

NUMERO_TRAMOS = 5

# Gráfico D: MAE de cada paso del modelado, tal como aparece en las salidas
# guardadas de modeling.ipynb. "cv" = validación cruzada de 5 folds sobre train;
# "test" = conjunto de test. El último punto es el modelo desplegado.
SERIE_MAE_POR_MODELO = (
    ("Regresión lineal", "Linear regression", 356_861.28000447544, "cv", 7),
    ("XGBoost", "XGBoost", 220_515.5375, "cv", 13),
    ("LightGBM", "LightGBM", 223_028.11612775121, "cv", 17),
    ("CatBoost", "CatBoost", 201_014.4791617237, "cv", 20),
    ("CatBoost, log del precio", "CatBoost, log price", 190_148.99762636214, "cv", 21),
    ("CatBoost + Optuna", "CatBoost + Optuna", 185_803.1288026239, "cv", 25),
    ("CatBoost + Optuna + tags", "CatBoost + Optuna + tags", 178_583.90321007842, "cv", 31),
    ("Modelo final", "Final model", 180_709.77338622112, "test", 36),
)


class InformeIncoherenteError(Exception):
    """Lo calculado no coincide con lo documentado o con la API."""


def predecir_test(modelo, train: pd.DataFrame, test: pd.DataFrame) -> tuple:
    """Precio real y predicho de test, procesado como en el notebook."""
    columnas = list(modelo.regressor_.feature_names_)
    test_procesado = anadir_columnas_tag(test, calcular_etiquetas_utiles(train))
    reales = test["PrecioActual"].to_numpy(dtype=float)
    predichos = modelo.predict(test_procesado[columnas])
    return reales, np.asarray(predichos, dtype=float)


def calcular_metricas(reales: np.ndarray, predichos: np.ndarray) -> dict:
    return {
        "mae": round(float(mean_absolute_error(reales, predichos)), DECIMALES_METRICAS["mae"]),
        "rmse": round(
            float(np.sqrt(mean_squared_error(reales, predichos))), DECIMALES_METRICAS["rmse"]
        ),
        "r2": round(float(r2_score(reales, predichos)), DECIMALES_METRICAS["r2"]),
    }


def comprobar_metricas(metricas: dict) -> None:
    for nombre, documentada in METRICAS_DOCUMENTADAS.items():
        if round(metricas[nombre], DECIMALES_DOCUMENTADOS[nombre]) != documentada:
            raise InformeIncoherenteError(
                f"{nombre} calculado {metricas[nombre]} distinto del documentado {documentada}"
            )


def calcular_tramos(reales: np.ndarray, predichos: np.ndarray) -> list[dict]:
    """Quintiles de precio real con su MAE, precio mediano y error relativo."""
    analisis = pd.DataFrame(
        {
            "real": reales,
            "error_abs": np.abs(reales - predichos),
            "tramo": pd.qcut(reales, q=NUMERO_TRAMOS),
        }
    )
    resumen = analisis.groupby("tramo", observed=True).agg(
        precio_mediano=("real", "median"), mae=("error_abs", "mean"), viviendas=("real", "size")
    )
    tramos = []
    for intervalo, fila in resumen.iterrows():
        tramos.append(
            {
                "limite_inferior": round(float(intervalo.left)),
                "limite_superior": round(float(intervalo.right)),
                "viviendas": int(fila["viviendas"]),
                "precio_mediano": round(float(fila["precio_mediano"])),
                "mae": round(float(fila["mae"])),
                "error_relativo": round(float(fila["mae"] / fila["precio_mediano"]), 4),
            }
        )
    return tramos


def comprobar_coherencia_con_api(
    tramos: list[dict], tramos_api: tuple[tuple[int, float], ...] = TRAMOS_ERROR
) -> None:
    """Los cortes y los márgenes redondeados deben ser los de la horquilla de la API."""
    if len(tramos) != len(tramos_api):
        raise InformeIncoherenteError("Distinto número de tramos que en la API")
    for posicion, tramo in enumerate(tramos):
        limite_api, margen_api = tramos_api[posicion]
        if posicion > 0 and tramo["limite_inferior"] != limite_api:
            raise InformeIncoherenteError(
                f"Tramo {posicion}: corte {tramo['limite_inferior']} "
                f"distinto de la API {limite_api}"
            )
        if round(tramo["error_relativo"], 2) != margen_api:
            raise InformeIncoherenteError(
                f"Tramo {posicion}: error {tramo['error_relativo']} distinto de la API {margen_api}"
            )


def puntos_real_predicho(reales: np.ndarray, predichos: np.ndarray) -> dict:
    """Pares en euros enteros, ordenados por precio real para un orden estable."""
    orden = np.argsort(reales, kind="stable")
    lista_reales = []
    lista_predichos = []
    for indice in orden:
        lista_reales.append(round(float(reales[indice])))
        lista_predichos.append(round(float(predichos[indice])))
    return {"reales": lista_reales, "predichos": lista_predichos}


def etiqueta_variable(columna: str) -> dict:
    """Etiqueta legible de los campos principales; las binarias se muestran por su nombre."""
    for campo in CAMPOS:
        if campo.columna == columna:
            return {"es": campo.etiqueta.es, "en": campo.etiqueta.en}
    return {"es": columna, "en": columna}


def calcular_importancias(modelo) -> list[dict]:
    """Importancia de cada variable (suma 100), de mayor a menor; empates por nombre."""
    columnas = list(modelo.regressor_.feature_names_)
    valores = modelo.regressor_.get_feature_importance()
    importancias = []
    for columna, valor in zip(columnas, valores, strict=True):
        importancias.append(
            {
                "columna": columna,
                "etiqueta": etiqueta_variable(columna),
                "importancia": round(float(valor), 3),
            }
        )
    importancias.sort(key=clave_orden_importancia)
    return importancias


def clave_orden_importancia(variable: dict) -> tuple[float, str]:
    """Mayor importancia primero; a igualdad, orden alfabético de la columna."""
    return (-variable["importancia"], variable["columna"])


def serie_mae_por_modelo() -> list[dict]:
    serie = []
    for nombre_es, nombre_en, mae, conjunto, celda in SERIE_MAE_POR_MODELO:
        serie.append(
            {
                "modelo": {"es": nombre_es, "en": nombre_en},
                "mae": round(mae),
                "conjunto": conjunto,
                "origen": f"modeling.ipynb, celda {celda}",
            }
        )
    return serie


def construir_informe(modelo, train: pd.DataFrame, test: pd.DataFrame) -> dict:
    reales, predichos = predecir_test(modelo, train, test)
    metricas = calcular_metricas(reales, predichos)
    comprobar_metricas(metricas)
    tramos = calcular_tramos(reales, predichos)
    comprobar_coherencia_con_api(tramos)

    serie = serie_mae_por_modelo()
    if serie[-1]["mae"] != round(metricas["mae"]):
        raise InformeIncoherenteError("El último punto del gráfico D no es el MAE calculado")

    regresor = modelo.regressor_
    return {
        "modelo": {
            "biblioteca": "catboost",
            "version": catboost.__version__,
            "arboles": int(regresor.tree_count_),
            "profundidad": int(regresor.get_all_params()["depth"]),
            "variables": len(regresor.feature_names_),
            "datos": "Idealista Madrid 2025",
            "viviendas_test": len(reales),
        },
        "metricas_test": metricas,
        "error_por_tramo": tramos,
        "real_frente_a_predicho": puntos_real_predicho(reales, predichos),
        "importancia_variables": calcular_importancias(modelo),
        "mae_por_modelo": serie,
    }


def main() -> int:
    for ruta in (RUTA_TRAIN, RUTA_TEST):
        if not ruta.is_file():
            print(f"ERROR: no existe {ruta}")
            return 1
    modelo = joblib.load(RUTA_MODELO)
    try:
        informe = construir_informe(modelo, pd.read_csv(RUTA_TRAIN), pd.read_csv(RUTA_TEST))
    except InformeIncoherenteError as error:
        print(f"ERROR: {error}")
        return 1
    escribir(RUTA_INFORME, informe)
    print(f"Informe escrito en {RUTA_INFORME}")
    print(f"  Métricas test: {informe['metricas_test']}")
    for tramo in informe["error_por_tramo"]:
        print(
            f"  {tramo['limite_inferior']:>10} - {tramo['limite_superior']:>10}: "
            f"{tramo['error_relativo']:.4f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
