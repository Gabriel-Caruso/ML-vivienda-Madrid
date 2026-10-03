"""Ruta raíz: presentación mínima hasta que llegue la interfaz de la fase 2."""

from fastapi import APIRouter

from tasador.api.v1.rutas import PREFIJO_V1
from tasador.config import NOMBRE_APP, VERSION_APP
from tasador.schemas.servicio import RespuestaRaiz

router = APIRouter(tags=["servicio"])


@router.get("/", response_model=RespuestaRaiz, summary="Información del servicio")
def raiz() -> RespuestaRaiz:
    return RespuestaRaiz(
        name=NOMBRE_APP,
        version=VERSION_APP,
        docs="/docs",
        endpoints={
            "health": f"{PREFIJO_V1}/health",
            "metadata": f"{PREFIJO_V1}/metadata",
            "predict": f"{PREFIJO_V1}/predict",
        },
    )
