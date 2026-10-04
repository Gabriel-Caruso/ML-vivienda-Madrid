"""Contrato de GET /api/v1/metadata: todo lo necesario para construir el formulario."""

from pydantic import BaseModel, ConfigDict


class EtiquetaBilingue(BaseModel):
    model_config = ConfigDict(title="Label")

    es: str
    en: str


class Opcion(BaseModel):
    """Valor que se envía a la API y texto que se muestra."""

    model_config = ConfigDict(title="Choice")

    value: str
    label: EtiquetaBilingue


class Distrito(BaseModel):
    model_config = ConfigDict(title="District")

    value: str
    label: EtiquetaBilingue
    neighbourhoods: list[str]


class RangoNumerico(BaseModel):
    model_config = ConfigDict(title="Range")

    min: int
    max: int


class Campo(BaseModel):
    model_config = ConfigDict(title="Field")

    name: str
    label: EtiquetaBilingue
    required: bool
    range: RangoNumerico | None


class TipoInmueble(BaseModel):
    """Tipo de inmueble; is_house indica casa o chalet (sin planta, ascensor ni localización)."""

    model_config = ConfigDict(title="PropertyType")

    value: str
    label: EtiquetaBilingue
    is_house: bool


class OpcionBinaria(BaseModel):
    model_config = ConfigDict(title="BinaryOption")

    key: str
    label: EtiquetaBilingue


class GrupoOpciones(BaseModel):
    model_config = ConfigDict(title="OptionGroup")

    key: str
    label: EtiquetaBilingue
    options: list[OpcionBinaria]


class RespuestaMetadata(BaseModel):
    """Catálogo del formulario. Zonas y barrios ordenados ignorando tildes."""

    model_config = ConfigDict(title="MetadataResponse")

    fields: list[Campo]
    districts: list[Distrito]
    property_types: list[TipoInmueble]
    lift: list[Opcion]
    position: list[Opcion]
    floors: list[Opcion]
    option_groups: list[GrupoOpciones]
