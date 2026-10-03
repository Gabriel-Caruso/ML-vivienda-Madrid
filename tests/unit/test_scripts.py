"""Tests de las funciones puras de los scripts, con datos sintéticos.

No necesitan data/: los CSV no están en el repositorio ni en la CI.
"""

import math

import numpy as np
import pandas as pd
import pytest
from build_catalog import construir_catalogo, serializar_catalogo, valores_ordenados
from build_fixtures import es_expresable, seleccionar_filas, valor_serializable
from preprocesado_original import anadir_columnas_tag, calcular_etiquetas_utiles

from tasador.domain.catalogo import Catalogo, clave_orden_alfabetico


def train_sintetico():
    return pd.DataFrame(
        {
            "zona": ["centro", "centro", "latina", "latina"],
            "barrio": ["Sol", "Palacio", "Águilas", "Aluche"],
            "tipo_inmueble": ["Piso", "Ático", "Piso", "Chalet"],
            "ascensor_limpio": ["S", "N", "S", "NO_APLICA"],
            "localizacion_limpio": ["EXTERIOR", "INTERIOR", "EXTERIOR", "NO_APLICA"],
            "planta_limpio": ["3ª", "BAJO", "-1", "NO_APLICA"],
        }
    )


# preprocesado_original


def test_etiquetas_utiles_respetan_umbral_y_orden_de_frecuencia():
    tags = ["TERRAZA, GARAJE"] * 150 + ["TERRAZA"] * 50 + ["PISCINA"] * 99 + [None]
    etiquetas = calcular_etiquetas_utiles(pd.DataFrame({"tags": tags}))
    assert etiquetas == ["TERRAZA", "GARAJE"]


def test_columnas_tag_como_en_el_notebook():
    df = pd.DataFrame({"tags": ["TERRAZA, SOLO_PARTICULARES", None, "GARAJE"]})
    resultado = anadir_columnas_tag(df, ["TERRAZA", "SOLO_PARTICULARES"])
    assert list(resultado["tag_terraza"]) == [1, 0, 0]
    assert list(resultado["tag_solo_particulares"]) == [1, 0, 0]
    assert "tag_terraza" not in df.columns


# build_catalog


def test_catalogo_agrupa_barrios_por_zona_ordenados():
    catalogo = construir_catalogo(train_sintetico(), "hash")
    assert catalogo["zonas"] == [
        {"zona": "centro", "barrios": ["Palacio", "Sol"]},
        {"zona": "latina", "barrios": ["Águilas", "Aluche"]},
    ]
    assert catalogo["plantas"] == ["-1", "BAJO", "3ª", "NO_APLICA"]
    assert catalogo["origen"]["sha256"] == "hash"


def test_catalogo_falla_si_un_barrio_esta_en_dos_zonas():
    train = train_sintetico()
    train.loc[3, "barrio"] = "Sol"
    with pytest.raises(ValueError, match="Sol"):
        construir_catalogo(train, "hash")


def test_serializacion_es_estable():
    catalogo = construir_catalogo(train_sintetico(), "hash")
    assert serializar_catalogo(catalogo) == serializar_catalogo(catalogo)
    assert serializar_catalogo(catalogo).endswith("\n")
    assert "Águilas" in serializar_catalogo(catalogo)


def test_valores_ordenados_descarta_nulos():
    serie = pd.Series(["Piso", None, "Ático", "Piso"])
    assert valores_ordenados(serie, clave_orden_alfabetico) == ["Ático", "Piso"]


# build_fixtures


def catalogo_sintetico():
    return Catalogo(
        barrios_por_zona={"centro": ("Sol",)},
        tipos_inmueble=("Piso",),
        ascensor=("S",),
        localizacion=("EXTERIOR",),
        plantas=("3ª",),
    )


def fila_expresable():
    return pd.Series(
        {
            "zona": "centro",
            "barrio": "Sol",
            "tipo_inmueble": "Piso",
            "ascensor_limpio": "S",
            "localizacion_limpio": "EXTERIOR",
            "planta_limpio": "3ª",
            "tag_terraza": 1,
            "tag_piso": 0,
            "tag_reformado": 1,
            "tag_reformada": 1,
            "tag_estrenar": 0,
            "tag_nuevo": 0,
        }
    )


COLUMNAS_BINARIAS = ["tag_terraza", "tag_piso", "tag_reformado", "tag_reformada"]


@pytest.fixture
def opciones_reducidas(monkeypatch):
    """Limita las opciones a las columnas de la fila sintética."""
    import build_fixtures

    from tasador.domain.tags import OPCIONES_BINARIAS

    reducidas = []
    for opcion in OPCIONES_BINARIAS:
        if set(opcion.columnas) <= set(fila_expresable().index):
            reducidas.append(opcion)
    monkeypatch.setattr(build_fixtures, "OPCIONES_BINARIAS", tuple(reducidas))


def test_fila_expresable(opciones_reducidas):
    assert es_expresable(fila_expresable(), COLUMNAS_BINARIAS, catalogo_sintetico())


def test_fila_con_tag_no_publico_no_es_expresable(opciones_reducidas):
    fila = fila_expresable()
    fila["tag_piso"] = 1
    assert not es_expresable(fila, COLUMNAS_BINARIAS, catalogo_sintetico())


def test_fila_con_sinonimo_sin_pareja_no_es_expresable(opciones_reducidas):
    fila = fila_expresable()
    fila["tag_reformada"] = 0
    assert not es_expresable(fila, COLUMNAS_BINARIAS, catalogo_sintetico())


def test_fila_con_barrio_de_otra_zona_no_es_expresable(opciones_reducidas):
    fila = fila_expresable()
    fila["zona"] = "latina"
    assert not es_expresable(fila, COLUMNAS_BINARIAS, catalogo_sintetico())


def test_fila_con_planta_fuera_de_catalogo_no_es_expresable(opciones_reducidas):
    fila = fila_expresable()
    fila["planta_limpio"] = "22ª"
    assert not es_expresable(fila, COLUMNAS_BINARIAS, catalogo_sintetico())


def candidatas_sinteticas():
    return pd.DataFrame(
        {
            "tipo_inmueble": ["Piso"] * 8 + ["Ático", "Estudio"],
            "zona": ["centro"] * 5 + ["latina", "retiro", "usera", "centro", "centro"],
            "baños_limpio": [np.nan] * 6 + [2.0, np.nan, 1.0, np.nan],
        },
        index=range(100, 110),
    )


def test_seleccion_reproducible_y_sin_repetidos():
    primera = seleccionar_filas(candidatas_sinteticas(), 6, 42)
    segunda = seleccionar_filas(candidatas_sinteticas(), 6, 42)
    assert primera == segunda
    assert len(primera) == len(set(primera)) == 6
    assert primera == sorted(primera)


def test_seleccion_prioriza_tipos_banos_y_zonas():
    candidatas = candidatas_sinteticas()
    seleccion = candidatas.loc[seleccionar_filas(candidatas, 6, 42)]
    assert set(seleccion["tipo_inmueble"]) == {"Piso", "Ático", "Estudio"}
    assert seleccion["baños_limpio"].notna().sum() == 2
    assert set(seleccion["zona"]) == {"centro", "latina", "retiro", "usera"}


def test_valor_serializable():
    assert valor_serializable(float("nan")) is None
    assert valor_serializable(np.int64(3)) == 3
    assert isinstance(valor_serializable(np.int64(3)), int)
    assert valor_serializable(np.float64(2.0)) == 2.0
    assert valor_serializable("Piso") == "Piso"
    assert not math.isnan(valor_serializable(np.float64(1.5)))
