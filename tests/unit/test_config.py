"""Tests de la configuración de rutas."""

from tasador.config import RAIZ_PROYECTO, RUTA_MODELO


def test_raiz_proyecto_contiene_pyproject():
    assert (RAIZ_PROYECTO / "pyproject.toml").is_file()


def test_ruta_modelo_existe():
    assert RUTA_MODELO.is_file()
