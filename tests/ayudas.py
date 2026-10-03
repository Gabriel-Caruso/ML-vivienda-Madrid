"""Utilidades compartidas por los tests."""

import pandas as pd

from tasador.domain.reglas import TIPOS_CASA_O_CHALET, VALOR_NO_APLICA, VALORES_SIN_DATO
from tasador.domain.tags import OPCIONES_BINARIAS

# Tipos con los que pandas leyó data/test.csv en el notebook
TIPOS_ENTRENAMIENTO_NO_BINARIOS = {
    "metros": "int64",
    "baños_limpio": "float64",
    "habitaciones_limpio": "float64",
    "zona": "str",
    "tipo_inmueble": "str",
    "ascensor_limpio": "str",
    "localizacion_limpio": "str",
    "barrio": "str",
    "planta_limpio": "str",
}


def peticion_valida() -> dict:
    """Petición completa y válida de referencia."""
    return {
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


def a_entero_opcional(valor: float | None) -> int | None:
    if valor is None:
        return None
    return int(valor)


def a_opcional_publico(valor: str, tipo_inmueble: str) -> str | None:
    """Valor público de ascensor, localización o planta: sin dato pasa a null.

    Comprueba que el valor sin dato es el que la API reconstruiría a partir
    del tipo; si no, la fila no sería expresable.
    """
    if valor not in VALORES_SIN_DATO:
        return valor
    es_casa = tipo_inmueble in TIPOS_CASA_O_CHALET
    assert (valor == VALOR_NO_APLICA) == es_casa, f"{valor} no encaja con {tipo_inmueble}"
    return None


def peticion_desde_fila(valores: dict) -> dict:
    """Petición pública equivalente a una fila del modelo (fixture)."""
    tipo = valores["tipo_inmueble"]
    opciones = []
    for opcion in OPCIONES_BINARIAS:
        activas = 0
        for columna in opcion.columnas:
            activas += valores[columna]
        if activas == len(opcion.columnas):
            opciones.append(opcion.clave)
    return {
        "area_m2": valores["metros"],
        "bathrooms": a_entero_opcional(valores["baños_limpio"]),
        "rooms": a_entero_opcional(valores["habitaciones_limpio"]),
        "district": valores["zona"],
        "neighbourhood": valores["barrio"],
        "property_type": tipo,
        "lift": a_opcional_publico(valores["ascensor_limpio"], tipo),
        "position": a_opcional_publico(valores["localizacion_limpio"], tipo),
        "floor": a_opcional_publico(valores["planta_limpio"], tipo),
        "options": opciones,
    }


def fila_como_en_entrenamiento(valores: dict, columnas: list[str]) -> pd.DataFrame:
    """DataFrame de una fila del fixture con los tipos que tenía en el notebook."""
    tipos = {}
    for columna in columnas:
        tipos[columna] = TIPOS_ENTRENAMIENTO_NO_BINARIOS.get(columna, "int64")
    return pd.DataFrame([valores], columns=columnas).astype(tipos)
