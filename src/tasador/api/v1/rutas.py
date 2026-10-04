"""Rutas de la versión 1 de la API.

Solo reciben, validan (mediante los esquemas) y responden: la lógica está en
services/ y el conocimiento del problema en domain/.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from tasador.api.dependencias import obtener_predictor
from tasador.config import NOMBRE_APP, VERSION_APP
from tasador.schemas.errores import CodigoError, DetalleError, RespuestaErrores
from tasador.schemas.metadata import RespuestaMetadata
from tasador.schemas.prediccion import PeticionPrediccion, RespuestaPrediccion
from tasador.schemas.servicio import RespuestaRaiz, RespuestaSalud
from tasador.services.metadata import construir_metadata
from tasador.services.predictor import Predictor

PREFIJO_V1 = "/api/v1"

router = APIRouter(prefix=PREFIJO_V1, tags=["v1"])

PredictorCargado = Annotated[Predictor | None, Depends(obtener_predictor)]


def respuesta_modelo_no_cargado() -> JSONResponse:
    respuesta = RespuestaErrores(
        errors=[
            DetalleError(
                code=CodigoError.MODEL_NOT_LOADED,
                field=None,
                message="Model is not loaded",
                params={},
            )
        ]
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=respuesta.model_dump(mode="json")
    )


@router.get("/", response_model=RespuestaRaiz, summary="Información del servicio")
def informacion() -> RespuestaRaiz:
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


@router.get(
    "/health",
    response_model=RespuestaSalud,
    responses={503: {"model": RespuestaSalud}},
    summary="Estado del servicio",
)
def health(predictor: PredictorCargado):
    if predictor is None:
        respuesta = RespuestaSalud(status="unavailable", model_loaded=False)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=respuesta.model_dump()
        )
    return RespuestaSalud(status="ok", model_loaded=True)


# HEAD además de GET: Render y los monitores de disponibilidad comprueban con HEAD.
# Se registra aparte y fuera del esquema para no duplicar la operación en /docs.
router.add_api_route("/health", health, methods=["HEAD"], include_in_schema=False)


@router.get(
    "/metadata",
    response_model=RespuestaMetadata,
    summary="Catálogo para construir el formulario",
)
def metadata() -> RespuestaMetadata:
    return construir_metadata()


@router.post(
    "/predict",
    response_model=RespuestaPrediccion,
    responses={
        422: {"model": RespuestaErrores, "description": "Petición no válida"},
        503: {"model": RespuestaErrores, "description": "Modelo no cargado"},
    },
    summary="Estimar el precio de una vivienda",
)
def predict(peticion: PeticionPrediccion, predictor: PredictorCargado):
    if predictor is None:
        return respuesta_modelo_no_cargado()
    prediccion = predictor.predecir(peticion)
    return RespuestaPrediccion(
        estimated_price=prediccion.precio,
        error_margin=prediccion.margen,
        price_min=prediccion.minimo,
        price_max=prediccion.maximo,
    )
