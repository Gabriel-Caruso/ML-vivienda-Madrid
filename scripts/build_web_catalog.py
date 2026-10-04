"""Exporta el catálogo del formulario como JSON estático para la web.

Es exactamente la respuesta de GET /api/v1/metadata, guardada en
src/tasador/web/datos/catalogo.json. Así el formulario funciona al instante
aunque la API esté dormida. No necesita data/: sale del dominio versionado.

Uso: uv run python scripts/build_web_catalog.py
"""

import sys

from salida_json import escribir

from tasador.config import RUTA_DATOS_WEB
from tasador.services.metadata import construir_metadata

RUTA_CATALOGO_WEB = RUTA_DATOS_WEB / "catalogo.json"


def construir_catalogo_web() -> dict:
    """Mismo contenido que devuelve la API en /api/v1/metadata."""
    return construir_metadata().model_dump(mode="json")


def main() -> int:
    catalogo = construir_catalogo_web()
    escribir(RUTA_CATALOGO_WEB, catalogo)
    print(f"Catálogo web escrito en {RUTA_CATALOGO_WEB}")
    print(f"  Distritos: {len(catalogo['districts'])}")
    print(f"  Grupos de opciones: {len(catalogo['option_groups'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
