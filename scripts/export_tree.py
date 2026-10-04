"""Exporta la estructura real del árbol 0 del CatBoost para el fondo de la web.

Escribe src/tasador/web/datos/arbol.json con:
- los 9 cortes del árbol, uno por nivel (los árboles de CatBoost son
  simétricos: todas las ramas de un nivel usan el mismo corte), con su variable
  y umbral reales, tal como los describe CatBoostRegressor.plot_tree;
- el recorrido de las viviendas de tests/fixtures/filas_referencia.json por el
  árbol, obtenido con CatBoostRegressor.calc_leaf_indexes.

Orden de niveles: el de plot_tree, de la raíz hacia abajo. En el índice de hoja
que devuelve calc_leaf_indexes, el nivel L corresponde al bit (profundidad - 1 - L)
y la rama "Yes" (condición cierta) al valor 1. El script lo comprueba en cada
ejecución con los cortes numéricos y binarios y falla si no se cumple.

Los cortes de variables categóricas no comparan la categoría: comparan un
estadístico del precio por categoría (CTR) discretizado. Se muestran como
"ctr(zona) > 3" en lugar de inventar una condición del tipo "zona = centro".

No necesita data/ y no modifica el modelo.

Uso: uv run python scripts/export_tree.py
"""

import json
import re
import sys
from pathlib import Path

import joblib
import pandas as pd
from catboost import Pool
from preprocesado_original import RUTA_MODELO
from salida_json import escribir

from tasador.config import RUTA_DATOS_WEB

RUTA_ARBOL = RUTA_DATOS_WEB / "arbol.json"
RUTA_FILAS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "filas_referencia.json"
INDICE_ARBOL = 0

PATRON_CORTE_NUMERICO = re.compile(r"^(?P<variable>[^{,]+), value>(?P<umbral>-?[\d.]+)$")
PATRON_CORTE_CTR = re.compile(
    r"^\{(?P<variable>[^}]+)\} counter_type=(?P<contador>\w+) "
    r"prior_numerator=(?P<prior>[\d.]+), value>(?P<umbral>-?[\d.]+)$"
)
PATRON_NODO = re.compile(r'^\s*(\w+)\s*\[label="([^"]*)"', re.MULTILINE)
PATRON_ARISTA = re.compile(r"^\s*(\w+)\s*->\s*(\w+)\s*\[label=(\w+)", re.MULTILINE)
PREFIJOS_BINARIOS = ("flag_", "tag_")
SUFIJO_LIMPIO = "_limpio"


class ArbolIncoherenteError(Exception):
    """La estructura extraída no encaja con lo que se espera de CatBoost."""


def nombre_visible(variable: str) -> str:
    """Nombre corto para el texto del fondo: "ascensor_limpio" -> "ascensor"."""
    return variable.removesuffix(SUFIJO_LIMPIO)


def describir_corte(etiqueta: str) -> dict:
    """Convierte la etiqueta de plot_tree en un corte estructurado."""
    numerico = PATRON_CORTE_NUMERICO.match(etiqueta)
    if numerico:
        variable = numerico.group("variable")
        umbral = float(numerico.group("umbral"))
        tipo = "binaria" if variable.startswith(PREFIJOS_BINARIOS) else "numerica"
        return {
            "variable": variable,
            "tipo": tipo,
            "umbral": umbral,
            "texto": f"{nombre_visible(variable)} > {numerico.group('umbral')}",
        }
    ctr = PATRON_CORTE_CTR.match(etiqueta)
    if ctr:
        variable = ctr.group("variable")
        return {
            "variable": variable,
            "tipo": "ctr",
            "umbral": float(ctr.group("umbral")),
            "texto": f"ctr({nombre_visible(variable)}) > {ctr.group('umbral')}",
        }
    raise ArbolIncoherenteError(f"Formato de corte no reconocido: {etiqueta!r}")


def etiquetas_por_nivel(fuente_dot: str) -> list[str]:
    """Etiqueta del corte de cada nivel, de la raíz hacia abajo.

    En un árbol simétrico todos los nodos de un nivel tienen el mismo corte,
    así que basta con bajar siempre por el primer hijo.
    """
    etiquetas_nodo = dict(PATRON_NODO.findall(fuente_dot))
    hijos = {}
    con_padre = set()
    for origen, destino, _ in PATRON_ARISTA.findall(fuente_dot):
        hijos.setdefault(origen, []).append(destino)
        con_padre.add(destino)
    raices = []
    for nodo in etiquetas_nodo:
        if nodo not in con_padre:
            raices.append(nodo)
    if len(raices) != 1:
        raise ArbolIncoherenteError(f"Se esperaba una raíz y hay {len(raices)}")

    etiquetas = []
    actual = raices[0]
    while actual in hijos:
        etiquetas.append(etiquetas_nodo[actual])
        actual = hijos[actual][0]
    return etiquetas


def ramas_desde_hoja(indice_hoja: int, profundidad: int) -> list[int]:
    """Rama tomada en cada nivel (1 = condición cierta) a partir del índice de hoja."""
    ramas = []
    for nivel in range(profundidad):
        ramas.append((indice_hoja >> (profundidad - 1 - nivel)) & 1)
    return ramas


def comprobar_ramas(niveles: list[dict], filas: pd.DataFrame, ramas_por_fila: list) -> None:
    """Las ramas deducidas del índice de hoja deben cumplir los cortes evaluables."""
    for posicion, ramas in enumerate(ramas_por_fila):
        for nivel, corte in enumerate(niveles):
            if corte["tipo"] == "ctr":
                continue
            valor = filas.iloc[posicion][corte["variable"]]
            esperada = int(not pd.isna(valor) and float(valor) > corte["umbral"])
            if ramas[nivel] != esperada:
                raise ArbolIncoherenteError(
                    f"Fila {posicion}, nivel {nivel}: rama {ramas[nivel]} y corte da {esperada}"
                )


def cargar_filas_referencia() -> tuple[pd.DataFrame, list[int]]:
    datos = json.loads(RUTA_FILAS.read_text(encoding="utf-8"))
    valores = []
    indices = []
    for fila in datos["filas"]:
        valores.append(fila["valores"])
        indices.append(fila["indice_test"])
    return pd.DataFrame(valores, columns=datos["columnas"]), indices


def construir_arbol(modelo, filas: pd.DataFrame, indices_test: list[int]) -> dict:
    regresor = modelo.regressor_
    columnas = list(regresor.feature_names_)
    categoricas = []
    for indice in regresor.get_cat_feature_indices():
        categoricas.append(columnas[indice])
    pool = Pool(filas[columnas], cat_features=categoricas)

    fuente = regresor.plot_tree(tree_idx=INDICE_ARBOL, pool=pool).source
    niveles = []
    for etiqueta in etiquetas_por_nivel(fuente):
        niveles.append(describir_corte(etiqueta))
    profundidad = int(regresor.get_all_params()["depth"])
    if len(niveles) != profundidad:
        raise ArbolIncoherenteError(f"{len(niveles)} niveles y profundidad {profundidad}")

    hojas = regresor.calc_leaf_indexes(pool, ntree_start=INDICE_ARBOL, ntree_end=INDICE_ARBOL + 1)
    ramas_por_fila = []
    for indice_hoja in hojas[:, 0]:
        ramas_por_fila.append(ramas_desde_hoja(int(indice_hoja), profundidad))
    comprobar_ramas(niveles, filas, ramas_por_fila)

    recorridos = []
    for indice_test, ramas in zip(indices_test, ramas_por_fila, strict=True):
        recorridos.append({"indice_test": indice_test, "ramas": ramas})

    return {
        "arbol": INDICE_ARBOL,
        "arboles_en_el_modelo": int(regresor.tree_count_),
        "profundidad": profundidad,
        "hojas": 2**profundidad,
        "niveles": niveles,
        "recorridos": recorridos,
    }


def main() -> int:
    modelo = joblib.load(RUTA_MODELO)
    filas, indices_test = cargar_filas_referencia()
    try:
        arbol = construir_arbol(modelo, filas, indices_test)
    except ArbolIncoherenteError as error:
        print(f"ERROR: {error}")
        return 1
    escribir(RUTA_ARBOL, arbol)
    print(f"Árbol {arbol['arbol']} escrito en {RUTA_ARBOL}")
    for nivel, corte in enumerate(arbol["niveles"]):
        print(f"  nivel {nivel}: {corte['texto']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
