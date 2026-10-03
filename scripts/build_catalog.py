"""Genera src/tasador/domain/catalogo.json a partir de data/train.csv.

El catálogo contiene los valores categóricos que vio el modelo: zonas con sus
barrios, tipos de inmueble, valores de ascensor y localización, y plantas.
Es reproducible: el mismo train.csv produce exactamente el mismo archivo
(listas ordenadas, sin fechas) y registra el hash del CSV de origen.

Uso: uv run python scripts/build_catalog.py
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
from preprocesado_original import RUTA_TRAIN

from tasador.config import RUTA_CATALOGO
from tasador.domain.catalogo import (
    VERSION_CATALOGO,
    clave_orden_alfabetico,
    clave_orden_planta,
)


def calcular_sha256(ruta: Path) -> str:
    """Hash del archivo de origen, para saber de qué datos sale el catálogo."""
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def construir_catalogo(train: pd.DataFrame, sha256_origen: str) -> dict:
    """Construye el catálogo como diccionario serializable a JSON.

    Falla si algún barrio aparece en más de una zona: la API depende de que
    cada barrio pertenezca a una sola.
    """
    zonas_por_barrio = train.groupby("barrio")["zona"].unique()
    barrios_repetidos = []
    for barrio, zonas in zonas_por_barrio.items():
        if len(zonas) > 1:
            barrios_repetidos.append(barrio)
    if barrios_repetidos:
        raise ValueError(f"Barrios presentes en más de una zona: {barrios_repetidos}")

    zonas = []
    for zona in sorted(train["zona"].unique(), key=clave_orden_alfabetico):
        barrios_zona = train.loc[train["zona"] == zona, "barrio"].unique()
        barrios_ordenados = sorted(barrios_zona, key=clave_orden_alfabetico)
        zonas.append({"zona": str(zona), "barrios": [str(b) for b in barrios_ordenados]})

    return {
        "version": VERSION_CATALOGO,
        "origen": {"archivo": "data/train.csv", "sha256": sha256_origen},
        "zonas": zonas,
        "tipos_inmueble": valores_ordenados(train["tipo_inmueble"], clave_orden_alfabetico),
        "ascensor": valores_ordenados(train["ascensor_limpio"], clave_orden_alfabetico),
        "localizacion": valores_ordenados(train["localizacion_limpio"], clave_orden_alfabetico),
        "plantas": valores_ordenados(train["planta_limpio"], clave_orden_planta),
    }


def valores_ordenados(columna: pd.Series, clave) -> list[str]:
    """Valores distintos y no nulos de una columna, como texto y ordenados."""
    valores = []
    for valor in columna.dropna().unique():
        valores.append(str(valor))
    return sorted(valores, key=clave)


def serializar_catalogo(catalogo: dict) -> str:
    """JSON legible y estable: mismas entradas, mismo texto."""
    return json.dumps(catalogo, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    if not RUTA_TRAIN.is_file():
        print(f"ERROR: no existe {RUTA_TRAIN}")
        return 1
    train = pd.read_csv(RUTA_TRAIN)
    catalogo = construir_catalogo(train, calcular_sha256(RUTA_TRAIN))
    RUTA_CATALOGO.write_text(serializar_catalogo(catalogo), encoding="utf-8", newline="\n")

    numero_barrios = 0
    for zona in catalogo["zonas"]:
        numero_barrios += len(zona["barrios"])
    print(f"Catálogo escrito en {RUTA_CATALOGO}")
    print(f"  Zonas: {len(catalogo['zonas'])}  Barrios: {numero_barrios}")
    print(f"  Tipos de inmueble: {len(catalogo['tipos_inmueble'])}")
    print(f"  Plantas: {len(catalogo['plantas'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
