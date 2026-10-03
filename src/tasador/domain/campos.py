"""Campos principales del contrato público y su columna en el modelo.

Es el único sitio donde se relaciona el nombre público de un campo (inglés,
snake_case) con el nombre de la columna del modelo. Las opciones binarias
tienen su propia correspondencia en tags.py.
"""

from dataclasses import dataclass

from tasador.domain.etiquetas import Etiqueta


@dataclass(frozen=True)
class Campo:
    """Campo del formulario y columna del modelo que alimenta."""

    nombre: str
    columna: str
    etiqueta: Etiqueta


CAMPO_METROS = Campo("area_m2", "metros", Etiqueta(es="Metros cuadrados", en="Square metres"))
CAMPO_HABITACIONES = Campo(
    "rooms", "habitaciones_limpio", Etiqueta(es="Habitaciones", en="Bedrooms")
)
CAMPO_BANOS = Campo("bathrooms", "baños_limpio", Etiqueta(es="Baños", en="Bathrooms"))
CAMPO_ZONA = Campo("district", "zona", Etiqueta(es="Distrito", en="District"))
CAMPO_BARRIO = Campo("neighbourhood", "barrio", Etiqueta(es="Barrio", en="Neighbourhood"))
CAMPO_TIPO = Campo(
    "property_type", "tipo_inmueble", Etiqueta(es="Tipo de inmueble", en="Property type")
)
CAMPO_ASCENSOR = Campo("lift", "ascensor_limpio", Etiqueta(es="Ascensor", en="Lift"))
CAMPO_LOCALIZACION = Campo(
    "position",
    "localizacion_limpio",
    Etiqueta(es="Exterior / interior", en="Exterior / interior"),
)
CAMPO_PLANTA = Campo("floor", "planta_limpio", Etiqueta(es="Planta", en="Floor"))

# Mismo orden que las columnas del modelo
CAMPOS = (
    CAMPO_METROS,
    CAMPO_BANOS,
    CAMPO_HABITACIONES,
    CAMPO_ZONA,
    CAMPO_TIPO,
    CAMPO_ASCENSOR,
    CAMPO_LOCALIZACION,
    CAMPO_BARRIO,
    CAMPO_PLANTA,
)
