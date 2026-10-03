"""Réplica de las partes del preprocesado original que no están en los CSV.

Los CSV de train y test ya traen las columnas limpias y los flags, pero no las
columnas tag_*: en el notebook de modelado se generaban a partir de la columna
"tags" en bruto. Este módulo reproduce ese código tal cual para que los scripts
puedan reconstruir las filas exactamente como las vio el modelo.

No forma parte del servicio: la API recibe los tags ya como 0/1.
"""

from pathlib import Path

import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_TRAIN = RAIZ_PROYECTO / "data" / "train.csv"
RUTA_TEST = RAIZ_PROYECTO / "data" / "test.csv"
RUTA_MODELO = RAIZ_PROYECTO / "models" / "catboost_madrid.joblib"
RUTA_MODELO_PKL = RAIZ_PROYECTO / "data" / "catboost_madrid.pkl"

# Mínimo de anuncios en los que debe aparecer una etiqueta (criterio del notebook)
FRECUENCIA_MINIMA_ETIQUETA = 100


def calcular_etiquetas_utiles(train: pd.DataFrame) -> list[str]:
    """Devuelve las etiquetas útiles en el mismo orden que en el notebook.

    El orden importa: es el de value_counts() sobre train y coincide con el
    orden de las columnas tag_* del modelo.
    """
    todas_etiquetas = train["tags"].fillna("").str.split(",").explode().str.strip()
    todas_etiquetas = todas_etiquetas[todas_etiquetas != ""]
    frecuencia = todas_etiquetas.value_counts()
    return frecuencia[frecuencia >= FRECUENCIA_MINIMA_ETIQUETA].index.tolist()


def anadir_columnas_tag(df: pd.DataFrame, etiquetas: list[str]) -> pd.DataFrame:
    """Añade una columna tag_<etiqueta> (0/1) por etiqueta, como en el notebook."""
    resultado = df.copy()
    tags_texto = resultado["tags"].fillna("")
    for etiqueta in etiquetas:
        columna = "tag_" + etiqueta.lower()
        resultado[columna] = tags_texto.str.contains(etiqueta, regex=False).astype(int)
    return resultado
