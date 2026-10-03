"""Configuración del servicio: rutas, identidad de la app y horquilla de precio.

Las rutas se calculan a partir de la ubicación de este archivo, nunca del
directorio desde el que se lanza el programa.
"""

from importlib.metadata import version
from pathlib import Path

# src/tasador/config.py -> parents[0] = tasador, parents[1] = src, parents[2] = raíz
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

RUTA_MODELO = RAIZ_PROYECTO / "models" / "catboost_madrid.joblib"

# Catálogo generado por scripts/build_catalog.py; vive dentro del paquete
RUTA_CATALOGO = Path(__file__).resolve().parent / "domain" / "catalogo.json"

NOMBRE_APP = "Tasador de vivienda en Madrid"
VERSION_APP = version("tasador-madrid")

# Horquilla de precio: error relativo según el tramo del precio predicho.
# Cada tramo es (límite inferior incluido en euros, margen relativo) y se aplica
# hasta el límite inferior del siguiente. El primero empieza en 0 y el último no
# tiene techo, de modo que los precios fuera de la tabla usan el tramo más cercano.
# PROVISIONAL: valores del README de ML-idealista, pendientes de recalcular con
# el modelo joblib (docs/DECISIONES.md, D-018).
TRAMOS_ERROR = (
    (0, 0.16),
    (250_000, 0.15),
    (435_360, 0.16),
    (835_600, 0.15),
    (1_490_000, 0.24),
)
