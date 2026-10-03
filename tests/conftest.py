"""Fixtures compartidas por todos los tests."""

import joblib
import pytest

from tasador.config import RUTA_MODELO


@pytest.fixture(scope="session")
def modelo():
    """Modelo cargado una sola vez para toda la sesión de tests."""
    return joblib.load(RUTA_MODELO)
