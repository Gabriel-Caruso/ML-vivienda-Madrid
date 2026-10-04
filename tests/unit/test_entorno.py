"""Tests del entorno: las versiones instaladas son las del entrenamiento.

Las versiones de referencia salen del requirements.txt del repositorio de
entrenamiento (Gabriel-Caruso/ML-idealista). Si alguna cambia, el modelo
serializado podría cargarse con avisos o predecir distinto.
"""

import sys
from importlib.metadata import version

import pytest

VERSION_PYTHON_ENTRENAMIENTO = (3, 14, 4)

# Dependencias directas del modelo y dependencias indirectas fijadas por restricción
VERSIONES_ENTRENAMIENTO = {
    "catboost": "1.2.10",
    "scikit-learn": "1.9.0",
    "pandas": "3.0.3",
    "numpy": "2.5.1",
    "joblib": "1.5.3",
    "contourpy": "1.3.3",
    "fonttools": "4.63.0",
    "kiwisolver": "1.5.0",
    "matplotlib": "3.11.0",
    "narwhals": "2.23.0",
    "packaging": "26.2",
    "plotly": "6.9.0",
    "pyparsing": "3.3.2",
    "scipy": "1.18.0",
    "threadpoolctl": "3.6.0",
}

# pandas solo depende de tzdata en Windows (marcador sys_platform == 'win32' en
# uv.lock): en Linux (CI y Render) no se instala y no hay versión que comprobar.
VERSION_TZDATA_ENTRENAMIENTO = "2026.2"


def test_version_python_es_la_del_entrenamiento():
    assert sys.version_info[:3] == VERSION_PYTHON_ENTRENAMIENTO


@pytest.mark.parametrize(("paquete", "version_esperada"), VERSIONES_ENTRENAMIENTO.items())
def test_version_instalada_es_la_del_entrenamiento(paquete, version_esperada):
    assert version(paquete) == version_esperada


@pytest.mark.skipif(sys.platform != "win32", reason="tzdata solo se instala en Windows")
def test_version_tzdata_en_windows():
    assert version("tzdata") == VERSION_TZDATA_ENTRENAMIENTO
