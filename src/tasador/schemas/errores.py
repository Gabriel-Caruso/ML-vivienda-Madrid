"""Códigos de error estables y forma de las respuestas de error.

Los códigos son parte del contrato: la interfaz los traduce. El campo
"message" es solo orientativo para quien use la API directamente.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class CodigoError(StrEnum):
    """Códigos de error que puede devolver la API."""

    INVALID_JSON = "INVALID_JSON"
    FIELD_REQUIRED = "FIELD_REQUIRED"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_VALUE = "INVALID_VALUE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    BATHROOMS_ZERO = "BATHROOMS_ZERO"
    VALUE_NOT_IN_CATALOG = "VALUE_NOT_IN_CATALOG"
    BARRIO_NOT_IN_ZONE = "BARRIO_NOT_IN_ZONE"
    UNKNOWN_OPTION = "UNKNOWN_OPTION"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    MODEL_NOT_LOADED = "MODEL_NOT_LOADED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class DetalleError(BaseModel):
    """Un error concreto de la petición."""

    model_config = ConfigDict(title="ErrorDetail")

    code: CodigoError
    field: str | None
    message: str
    params: dict


class RespuestaErrores(BaseModel):
    """Respuesta de error: siempre una lista, aunque haya un solo error."""

    model_config = ConfigDict(title="ErrorResponse")

    errors: list[DetalleError]
