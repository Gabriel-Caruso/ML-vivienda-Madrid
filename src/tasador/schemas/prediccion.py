"""Contrato público de POST /api/v1/predict.

Los nombres de campo están en inglés; los valores categóricos, en español,
tal como los conoce el modelo. Cada error de validación lleva un código
estable (ver errores.py) en lugar de una frase.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from tasador.domain.catalogo import cargar_catalogo, valores_seleccionables
from tasador.domain.rangos import RANGO_BANOS, RANGO_HABITACIONES, RANGO_METROS, Rango
from tasador.domain.tags import OPCIONES_BINARIAS
from tasador.schemas.errores import CodigoError


def claves_opciones() -> list[str]:
    claves = []
    for opcion in OPCIONES_BINARIAS:
        claves.append(opcion.clave)
    return claves


def validar_rango(valor: int | None, rango: Rango) -> int | None:
    if valor is not None and not rango.contiene(valor):
        raise PydanticCustomError(
            CodigoError.OUT_OF_RANGE.value,
            "Value must be between {min} and {max}",
            {"min": rango.minimo, "max": rango.maximo},
        )
    return valor


def validar_en_catalogo(valor: str | None, validos: tuple[str, ...]) -> str | None:
    if valor is not None and valor not in validos:
        raise PydanticCustomError(
            CodigoError.VALUE_NOT_IN_CATALOG.value,
            "Value '{value}' is not in the catalog",
            {"value": valor},
        )
    return valor


def esquema_rango(rango: Rango) -> dict:
    """Límites para la documentación de Swagger (la validación la hacen los validadores)."""
    return {"minimum": rango.minimo, "maximum": rango.maximo}


class PeticionPrediccion(BaseModel):
    """Características de la vivienda a tasar."""

    model_config = ConfigDict(
        title="PredictionRequest",
        extra="forbid",
        strict=True,
        json_schema_extra={
            "examples": [
                {
                    "area_m2": 85,
                    "bathrooms": 2,
                    "rooms": 3,
                    "district": "chamberi",
                    "neighbourhood": "Trafalgar",
                    "property_type": "Piso",
                    "lift": "S",
                    "position": "EXTERIOR",
                    "floor": "3ª",
                    "options": ["terrace", "renovated"],
                }
            ]
        },
    )

    area_m2: int = Field(
        description="Superficie en metros cuadrados.",
        json_schema_extra=esquema_rango(RANGO_METROS),
    )
    bathrooms: int | None = Field(
        default=None,
        description="Número de baños; null si se desconoce. El 0 no se admite.",
        json_schema_extra=esquema_rango(RANGO_BANOS),
    )
    rooms: int | None = Field(
        default=None,
        description="Número de habitaciones (0 en estudios); null si se desconoce.",
        json_schema_extra=esquema_rango(RANGO_HABITACIONES),
    )
    district: str = Field(description="Zona (distrito), por ejemplo 'centro'.")
    neighbourhood: str = Field(description="Barrio; debe pertenecer a la zona.")
    property_type: str = Field(description="Tipo de inmueble, por ejemplo 'Piso'.")
    lift: str | None = Field(default=None, description="'S' o 'N'; null si se desconoce.")
    position: str | None = Field(
        default=None, description="'EXTERIOR' o 'INTERIOR'; null si se desconoce."
    )
    floor: str | None = Field(
        default=None, description="Planta, por ejemplo 'BAJO' o '3ª'; null si se desconoce."
    )
    options: list[str] = Field(
        default_factory=list,
        description="Casillas activadas de 'más opciones'. Las no enviadas valen 0.",
        json_schema_extra={"items": {"type": "string", "enum": claves_opciones()}},
    )

    @field_validator("area_m2")
    @classmethod
    def validar_metros(cls, valor: int) -> int:
        return validar_rango(valor, RANGO_METROS)

    @field_validator("bathrooms")
    @classmethod
    def validar_banos(cls, valor: int | None) -> int | None:
        if valor == 0:
            raise PydanticCustomError(
                CodigoError.BATHROOMS_ZERO.value,
                "Bathrooms cannot be 0; send null if unknown",
            )
        return validar_rango(valor, RANGO_BANOS)

    @field_validator("rooms")
    @classmethod
    def validar_habitaciones(cls, valor: int | None) -> int | None:
        return validar_rango(valor, RANGO_HABITACIONES)

    @field_validator("district")
    @classmethod
    def validar_zona(cls, valor: str) -> str:
        return validar_en_catalogo(valor, cargar_catalogo().zonas)

    @field_validator("neighbourhood")
    @classmethod
    def validar_barrio(cls, valor: str) -> str:
        if not cargar_catalogo().es_barrio_conocido(valor):
            raise PydanticCustomError(
                CodigoError.VALUE_NOT_IN_CATALOG.value,
                "Value '{value}' is not in the catalog",
                {"value": valor},
            )
        return valor

    @field_validator("property_type")
    @classmethod
    def validar_tipo(cls, valor: str) -> str:
        return validar_en_catalogo(valor, cargar_catalogo().tipos_inmueble)

    @field_validator("lift")
    @classmethod
    def validar_ascensor(cls, valor: str | None) -> str | None:
        return validar_en_catalogo(valor, valores_seleccionables(cargar_catalogo().ascensor))

    @field_validator("position")
    @classmethod
    def validar_localizacion(cls, valor: str | None) -> str | None:
        return validar_en_catalogo(valor, valores_seleccionables(cargar_catalogo().localizacion))

    @field_validator("floor")
    @classmethod
    def validar_planta(cls, valor: str | None) -> str | None:
        return validar_en_catalogo(valor, valores_seleccionables(cargar_catalogo().plantas))

    @field_validator("options")
    @classmethod
    def validar_opciones(cls, valor: list[str]) -> list[str]:
        validas = claves_opciones()
        for clave in valor:
            if clave not in validas:
                raise PydanticCustomError(
                    CodigoError.UNKNOWN_OPTION.value,
                    "Unknown option '{value}'",
                    {"value": clave},
                )
        return valor

    @model_validator(mode="after")
    def validar_barrio_en_zona(self) -> PeticionPrediccion:
        if not cargar_catalogo().barrio_pertenece_a_zona(self.neighbourhood, self.district):
            raise PydanticCustomError(
                CodigoError.BARRIO_NOT_IN_ZONE.value,
                "Neighbourhood '{neighbourhood}' does not belong to district '{district}'",
                {
                    "field": "neighbourhood",
                    "neighbourhood": self.neighbourhood,
                    "district": self.district,
                },
            )
        return self


class RespuestaPrediccion(BaseModel):
    """Precio estimado y horquilla según el error del modelo en su tramo de precio."""

    model_config = ConfigDict(title="PredictionResponse")

    estimated_price: float = Field(description="Precio estimado en euros, sin redondear.")
    error_margin: float = Field(description="Margen relativo aplicado, por ejemplo 0.16.")
    price_min: float = Field(description="Extremo inferior de la horquilla, en euros.")
    price_max: float = Field(description="Extremo superior de la horquilla, en euros.")
