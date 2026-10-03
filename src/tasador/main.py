"""Punto de entrada: crea la aplicación FastAPI.

Arranque: uvicorn --factory tasador.main:create_app
El modelo se carga una sola vez, en el lifespan, antes de aceptar peticiones.
Si no se puede cargar, la app no arranca.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from tasador.api.errores import registrar_manejadores
from tasador.api.raiz import router as router_raiz
from tasador.api.v1.rutas import router as router_v1
from tasador.config import NOMBRE_APP, RUTA_MODELO, VERSION_APP
from tasador.services.predictor import Predictor

NOMBRE_LOGGER = "tasador"
FORMATO_LOG = "%(levelname)s:     %(name)s: %(message)s"


def configurar_logs() -> None:
    """Muestra los logs técnicos del paquete con el mismo estilo que uvicorn.

    Uvicorn solo configura sus propios loggers. Nunca se registra el contenido
    de las peticiones: solo carga del modelo y errores.
    """
    logger = logging.getLogger(NOMBRE_LOGGER)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter(FORMATO_LOG))
        logger.addHandler(manejador)


def create_app(ruta_modelo: Path = RUTA_MODELO) -> FastAPI:
    """Construye la app con sus rutas y manejadores de error."""
    configurar_logs()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.predictor = Predictor.desde_archivo(ruta_modelo)
        yield
        app.state.predictor = None

    app = FastAPI(
        title=NOMBRE_APP,
        version=VERSION_APP,
        description="Estima el precio de venta de una vivienda en Madrid con un modelo CatBoost.",
        lifespan=lifespan,
    )
    registrar_manejadores(app)
    app.include_router(router_raiz)
    app.include_router(router_v1)
    return app
