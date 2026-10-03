"""Configuración del servicio: rutas a los recursos del proyecto.

Las rutas se calculan a partir de la ubicación de este archivo, nunca del
directorio desde el que se lanza el programa.
"""

from pathlib import Path

# src/tasador/config.py -> parents[0] = tasador, parents[1] = src, parents[2] = raíz
RAIZ_PROYECTO = Path(__file__).resolve().parents[2]

RUTA_MODELO = RAIZ_PROYECTO / "models" / "catboost_madrid.joblib"
