"""Traducción de errores a respuestas con códigos estables.

Los errores de validación de Pydantic se convierten a la forma
{"errors": [{"code", "field", "message", "params"}]}. Los códigos propios
(BARRIO_NOT_IN_ZONE...) ya vienen como tipo del error; los de Pydantic se
agrupan en unos pocos códigos genéricos.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from tasador.schemas.errores import CodigoError, DetalleError, RespuestaErrores

logger = logging.getLogger(__name__)

CODIGOS_PROPIOS = frozenset(codigo.value for codigo in CodigoError)

CODIGOS_PYDANTIC = {
    "missing": CodigoError.FIELD_REQUIRED,
    "extra_forbidden": CodigoError.UNKNOWN_FIELD,
    "json_invalid": CodigoError.INVALID_JSON,
}

# Prefijo de la ruta de los errores del cuerpo de la petición
SEGMENTO_CUERPO = "body"


def codigo_para(tipo_error: str) -> CodigoError:
    """Código estable para un tipo de error de Pydantic."""
    if tipo_error in CODIGOS_PROPIOS:
        return CodigoError(tipo_error)
    if tipo_error in CODIGOS_PYDANTIC:
        return CODIGOS_PYDANTIC[tipo_error]
    if tipo_error.endswith(("_type", "_parsing")) or tipo_error == "int_from_float":
        return CodigoError.INVALID_TYPE
    return CodigoError.INVALID_VALUE


def campo_para(ubicacion: tuple, contexto: dict) -> str | None:
    """Campo afectado: el primer segmento tras "body", o el indicado en el contexto."""
    if "field" in contexto:
        return contexto["field"]
    segmentos = []
    for segmento in ubicacion:
        if segmento != SEGMENTO_CUERPO:
            segmentos.append(segmento)
    if segmentos and isinstance(segmentos[0], str):
        return segmentos[0]
    return None


def convertir_error(error: dict) -> DetalleError:
    contexto = dict(error.get("ctx") or {})
    parametros = {}
    for clave, valor in contexto.items():
        if clave != "field":
            parametros[clave] = valor if isinstance(valor, (str, int, float, bool)) else str(valor)
    return DetalleError(
        code=codigo_para(error["type"]),
        field=campo_para(tuple(error.get("loc", ())), contexto),
        message=error["msg"],
        params=parametros,
    )


async def manejar_validacion(request: Request, exc: RequestValidationError) -> JSONResponse:
    detalles = []
    for error in exc.errors():
        detalles.append(convertir_error(error))
    respuesta = RespuestaErrores(errors=detalles)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=respuesta.model_dump(mode="json")
    )


async def manejar_error_interno(request: Request, exc: Exception) -> JSONResponse:
    # Solo se registra el error técnico, nunca el contenido de la petición
    logger.exception("Error no controlado en %s %s", request.method, request.url.path)
    respuesta = RespuestaErrores(
        errors=[
            DetalleError(
                code=CodigoError.INTERNAL_ERROR,
                field=None,
                message="Internal server error",
                params={},
            )
        ]
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=respuesta.model_dump(mode="json")
    )


def registrar_manejadores(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, manejar_validacion)
    app.add_exception_handler(Exception, manejar_error_interno)
