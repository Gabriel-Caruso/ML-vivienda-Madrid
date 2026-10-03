"""Genera tests/fixtures/filas_referencia.json a partir de data/test.csv.

Selecciona 20 filas de test, procesadas exactamente como en el notebook
(tags reconstruidos desde la columna "tags" en bruto), y guarda solo las
columnas que usa el modelo, en su orden. No guarda título, descripción, URL
ni precio.

Solo se eligen filas "expresables" por la API: sin columnas binarias activas
fuera del contrato público, con los pares de sinónimos coherentes (las dos
columnas a 0 o las dos a 1) y con todos sus valores categóricos en el
catálogo. Así el test de referencia compara la API con model.predict() sobre
la fila del notebook sin ninguna transformación intermedia.

La selección es reproducible (random_state=42) y prioriza variedad:
primero todos los tipos de inmueble, luego todas las filas con baños y
después zonas aún no cubiertas.

Uso: uv run python scripts/build_fixtures.py
"""

import json
import math
import sys
from pathlib import Path

import joblib
import pandas as pd
from preprocesado_original import (
    RUTA_MODELO,
    RUTA_TEST,
    RUTA_TRAIN,
    anadir_columnas_tag,
    calcular_etiquetas_utiles,
)

from tasador.domain.catalogo import Catalogo, cargar_catalogo
from tasador.domain.tags import OPCIONES_BINARIAS, columnas_binarias_publicas

RUTA_FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "filas_referencia.json"
NUMERO_FILAS = 20
SEMILLA = 42


def es_expresable(fila: pd.Series, columnas_binarias: list[str], catalogo: Catalogo) -> bool:
    """Indica si la API puede reproducir la fila exacta a partir de una petición."""
    publicas = columnas_binarias_publicas()
    for columna in columnas_binarias:
        if columna not in publicas and fila[columna] != 0:
            return False

    for opcion in OPCIONES_BINARIAS:
        valores = set()
        for columna in opcion.columnas:
            valores.add(int(fila[columna]))
        if len(valores) > 1:
            return False

    if not catalogo.barrio_pertenece_a_zona(fila["barrio"], fila["zona"]):
        return False
    comprobaciones = [
        (fila["tipo_inmueble"], catalogo.tipos_inmueble),
        (fila["ascensor_limpio"], catalogo.ascensor),
        (fila["localizacion_limpio"], catalogo.localizacion),
        (fila["planta_limpio"], catalogo.plantas),
    ]
    for valor, valores_validos in comprobaciones:
        if valor not in valores_validos:
            return False
    return True


def seleccionar_filas(candidatas: pd.DataFrame, numero: int, semilla: int) -> list:
    """Elige índices de candidatas priorizando variedad, de forma reproducible."""
    mezcladas = candidatas.sample(frac=1, random_state=semilla)
    seleccion = []

    tipos_cubiertos = set()
    for indice, fila in mezcladas.iterrows():
        if fila["tipo_inmueble"] not in tipos_cubiertos:
            tipos_cubiertos.add(fila["tipo_inmueble"])
            seleccion.append(indice)

    for indice, fila in mezcladas.iterrows():
        if len(seleccion) >= numero:
            break
        if indice not in seleccion and not math.isnan(fila["baños_limpio"]):
            seleccion.append(indice)

    zonas_cubiertas = set(candidatas.loc[seleccion, "zona"])
    for indice, fila in mezcladas.iterrows():
        if len(seleccion) >= numero:
            break
        if indice not in seleccion and fila["zona"] not in zonas_cubiertas:
            zonas_cubiertas.add(fila["zona"])
            seleccion.append(indice)

    for indice in mezcladas.index:
        if len(seleccion) >= numero:
            break
        if indice not in seleccion:
            seleccion.append(indice)

    return sorted(seleccion[:numero])


def valor_serializable(valor):
    """Convierte un valor de pandas a JSON: NaN pasa a null y los enteros a int."""
    if isinstance(valor, float) and math.isnan(valor):
        return None
    if hasattr(valor, "item"):
        return valor.item()
    return valor


def construir_fixture(filas: pd.DataFrame, columnas_modelo: list[str]) -> dict:
    """Estructura del archivo de fixtures."""
    lista_filas = []
    for indice, fila in filas.iterrows():
        valores = {}
        for columna in columnas_modelo:
            valores[columna] = valor_serializable(fila[columna])
        lista_filas.append({"indice_test": int(indice), "valores": valores})
    return {
        "origen": "data/test.csv",
        "random_state": SEMILLA,
        "columnas": columnas_modelo,
        "filas": lista_filas,
    }


def main() -> int:
    for ruta in (RUTA_TRAIN, RUTA_TEST):
        if not ruta.is_file():
            print(f"ERROR: no existe {ruta}")
            return 1

    modelo = joblib.load(RUTA_MODELO)
    columnas_modelo = list(modelo.regressor_.feature_names_)
    columnas_binarias = []
    for columna in columnas_modelo:
        if columna.startswith(("flag_", "tag_")):
            columnas_binarias.append(columna)

    etiquetas = calcular_etiquetas_utiles(pd.read_csv(RUTA_TRAIN))
    test = anadir_columnas_tag(pd.read_csv(RUTA_TEST), etiquetas)
    catalogo = cargar_catalogo()

    expresables = []
    for indice, fila in test.iterrows():
        if es_expresable(fila, columnas_binarias, catalogo):
            expresables.append(indice)
    candidatas = test.loc[expresables]

    seleccion = seleccionar_filas(candidatas, NUMERO_FILAS, SEMILLA)
    filas = candidatas.loc[seleccion]
    fixture = construir_fixture(filas, columnas_modelo)

    RUTA_FIXTURES.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(fixture, ensure_ascii=False, indent=2) + "\n"
    RUTA_FIXTURES.write_text(texto, encoding="utf-8", newline="\n")

    print(f"Filas expresables en test: {len(candidatas)} de {len(test)}")
    print(f"Fixtures escritos en {RUTA_FIXTURES}: {len(filas)} filas")
    print(f"  Zonas: {filas['zona'].nunique()}  Tipos: {sorted(filas['tipo_inmueble'].unique())}")
    print(f"  Con baños: {int(filas['baños_limpio'].notna().sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
