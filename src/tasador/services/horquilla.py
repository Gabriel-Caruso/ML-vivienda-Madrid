"""Cálculo de la horquilla de precio a partir del precio predicho."""

from dataclasses import dataclass

from tasador.config import TRAMOS_ERROR


@dataclass(frozen=True)
class Horquilla:
    """Margen aplicado y precios mínimo y máximo resultantes."""

    margen: float
    minimo: float
    maximo: float


def comprobar_tramos(tramos: tuple[tuple[int, float], ...]) -> None:
    """Falla si los tramos no empiezan en 0 o no están en orden creciente."""
    if not tramos or tramos[0][0] != 0:
        raise ValueError("El primer tramo de error debe empezar en 0")
    limite_anterior = -1
    for limite, margen in tramos:
        if limite <= limite_anterior:
            raise ValueError("Los tramos de error deben estar en orden creciente")
        if not 0 < margen < 1:
            raise ValueError(f"Margen fuera de (0, 1): {margen}")
        limite_anterior = limite


def margen_para(precio: float, tramos: tuple[tuple[int, float], ...] = TRAMOS_ERROR) -> float:
    """Margen relativo del tramo en que cae el precio.

    Un precio exactamente en un límite pertenece al tramo que empieza en él.
    """
    comprobar_tramos(tramos)
    margen_aplicable = tramos[0][1]
    for limite, margen in tramos:
        if precio >= limite:
            margen_aplicable = margen
    return margen_aplicable


def calcular_horquilla(
    precio: float, tramos: tuple[tuple[int, float], ...] = TRAMOS_ERROR
) -> Horquilla:
    """Horquilla simétrica alrededor del precio predicho."""
    margen = margen_para(precio, tramos)
    return Horquilla(margen=margen, minimo=precio * (1 - margen), maximo=precio * (1 + margen))
