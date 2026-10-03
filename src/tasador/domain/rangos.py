"""Rangos válidos de las variables numéricas.

Se basan en la limpieza del notebook original y en los valores mínimo y
máximo de data/train.csv (metros 11-3015, habitaciones 0-20, baños 1-7).
Fuera de ellos el modelo no extrapola y la predicción no sería fiable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Rango:
    """Intervalo cerrado de enteros admitidos."""

    minimo: int
    maximo: int

    def contiene(self, valor: int) -> bool:
        return self.minimo <= valor <= self.maximo


RANGO_METROS = Rango(minimo=10, maximo=3100)
RANGO_HABITACIONES = Rango(minimo=0, maximo=20)
# El 0 no se admite: en el entrenamiento significaba "sin dato" y se convirtió en NaN
RANGO_BANOS = Rango(minimo=1, maximo=7)
