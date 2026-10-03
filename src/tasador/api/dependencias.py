"""Dependencias compartidas por las rutas."""

from fastapi import Request

from tasador.services.predictor import Predictor


def obtener_predictor(request: Request) -> Predictor | None:
    """Predictor cargado en el lifespan de la app, o None si no lo está."""
    return getattr(request.app.state, "predictor", None)
