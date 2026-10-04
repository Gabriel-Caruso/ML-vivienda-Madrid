"""Punto de entrada: crea la aplicación FastAPI.

Arranque: uvicorn --factory tasador.main:create_app
El modelo se carga una sola vez, en el lifespan, antes de aceptar peticiones.
Si no se puede cargar, la app no arranca.

La app sirve además la interfaz web estática en "/" y admite peticiones desde
otros orígenes (el Static Site de producción) solo si están en ALLOWED_ORIGINS.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tasador.api.errores import registrar_manejadores
from tasador.api.raiz import registrar_web
from tasador.api.v1.rutas import router as router_v1
from tasador.config import NOMBRE_APP, RUTA_MODELO, VERSION_APP, origenes_desde_entorno
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


def create_app(
    ruta_modelo: Path = RUTA_MODELO, origenes_permitidos: list[str] | None = None
) -> FastAPI:
    """Construye la app con sus rutas, manejadores de error, CORS y la web.

    Si no se indican los orígenes permitidos, se leen de ALLOWED_ORIGINS.
    """
    configurar_logs()
    if origenes_permitidos is None:
        origenes_permitidos = origenes_desde_entorno()

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origenes_permitidos,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(router_v1)
    # La web va al final: sus rutas no deben tapar las de la API
    registrar_web(app)
    return app
