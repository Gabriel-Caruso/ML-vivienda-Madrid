"""Fixtures compartidas por todos los tests."""

import json
from pathlib import Path

import joblib
import pytest
from fastapi.testclient import TestClient

from tasador.config import RUTA_MODELO
from tasador.domain.catalogo import cargar_catalogo
from tasador.main import create_app
from tasador.services.predictor import Predictor

RUTA_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "filas_referencia.json"


@pytest.fixture(scope="session")
def modelo():
    """Modelo cargado una sola vez para toda la sesión de tests."""
    return joblib.load(RUTA_MODELO)


@pytest.fixture(scope="session")
def catalogo():
    """Catálogo versionado en el paquete."""
    return cargar_catalogo()


@pytest.fixture(scope="session")
def predictor(modelo):
    """Servicio de predicción sobre el modelo de la sesión."""
    return Predictor(modelo)


@pytest.fixture(scope="session")
def cliente():
    """Cliente HTTP de la app; el context manager ejecuta el lifespan (carga del modelo)."""
    with TestClient(create_app()) as cliente_http:
        yield cliente_http


@pytest.fixture(scope="session")
def filas_referencia():
    """Contenido de tests/fixtures/filas_referencia.json."""
    return json.loads(RUTA_FIXTURES.read_text(encoding="utf-8"))
