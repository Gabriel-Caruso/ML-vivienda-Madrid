"""Contratos de GET / y GET /api/v1/health."""

from pydantic import BaseModel, ConfigDict


class RespuestaSalud(BaseModel):
    """Estado del servicio para el health check de Render."""

    model_config = ConfigDict(title="HealthResponse")

    status: str
    model_loaded: bool


class RespuestaRaiz(BaseModel):
    """Presentación mínima del servicio. La fase 2 la sustituirá por la interfaz."""

    model_config = ConfigDict(title="RootResponse")

    name: str
    version: str
    docs: str
    endpoints: dict[str, str]
