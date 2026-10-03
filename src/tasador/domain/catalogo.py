"""Catálogo de valores categóricos que conoce el modelo.

El catálogo se genera con scripts/build_catalog.py a partir de data/train.csv
y se guarda en catalogo.json, junto a este módulo. Aquí solo se lee: el
servicio no depende de los datos de entrenamiento.
"""

import json
import unicodedata
from dataclasses import dataclass
from functools import cache

from tasador.config import RUTA_CATALOGO
from tasador.domain.reglas import VALOR_DESCONOCIDO, VALOR_NO_APLICA, VALORES_SIN_DATO

VERSION_CATALOGO = 1


@dataclass(frozen=True)
class Catalogo:
    """Valores válidos de cada variable categórica del modelo."""

    barrios_por_zona: dict[str, tuple[str, ...]]
    tipos_inmueble: tuple[str, ...]
    ascensor: tuple[str, ...]
    localizacion: tuple[str, ...]
    plantas: tuple[str, ...]

    @property
    def zonas(self) -> tuple[str, ...]:
        return tuple(self.barrios_por_zona)

    def barrio_pertenece_a_zona(self, barrio: str, zona: str) -> bool:
        return barrio in self.barrios_por_zona.get(zona, ())

    def es_barrio_conocido(self, barrio: str) -> bool:
        for barrios in self.barrios_por_zona.values():
            if barrio in barrios:
                return True
        return False


def valores_seleccionables(valores: tuple[str, ...]) -> tuple[str, ...]:
    """Valores que el usuario puede elegir: todos menos DESCONOCIDO y NO_APLICA.

    Esos dos los asigna la API cuando el usuario no indica el dato.
    """
    seleccionables = []
    for valor in valores:
        if valor not in VALORES_SIN_DATO:
            seleccionables.append(valor)
    return tuple(seleccionables)


@cache
def cargar_catalogo() -> Catalogo:
    """Lee catalogo.json una sola vez por proceso."""
    datos = json.loads(RUTA_CATALOGO.read_text(encoding="utf-8"))
    if datos["version"] != VERSION_CATALOGO:
        raise ValueError(
            f"Versión de catálogo {datos['version']} no soportada (se esperaba {VERSION_CATALOGO})"
        )
    barrios_por_zona = {}
    for entrada in datos["zonas"]:
        barrios_por_zona[entrada["zona"]] = tuple(entrada["barrios"])
    return Catalogo(
        barrios_por_zona=barrios_por_zona,
        tipos_inmueble=tuple(datos["tipos_inmueble"]),
        ascensor=tuple(datos["ascensor"]),
        localizacion=tuple(datos["localizacion"]),
        plantas=tuple(datos["plantas"]),
    )


def clave_orden_alfabetico(texto: str) -> tuple[str, str]:
    """Clave para ordenar ignorando tildes y mayúsculas.

    Así "Águilas" queda junto a "Aluche" y no al final de la lista, que es lo
    que espera quien busca en un desplegable. El texto original desempata.
    """
    descompuesto = unicodedata.normalize("NFD", texto)
    letras = []
    for caracter in descompuesto:
        if unicodedata.category(caracter) != "Mn":
            letras.append(caracter)
    return "".join(letras).casefold(), texto


def clave_orden_planta(planta: str) -> tuple[int, int]:
    """Clave para ordenar plantas de abajo arriba.

    Orden: sótanos ("-2", "-1"), BAJO, ENTREPLANTA, plantas ordinales ("1ª",
    "2ª"...) y al final los valores sin dato.
    """
    if planta == VALOR_DESCONOCIDO:
        return (3, 0)
    if planta == VALOR_NO_APLICA:
        return (3, 1)
    if planta == "BAJO":
        return (1, 0)
    if planta == "ENTREPLANTA":
        return (1, 1)
    if planta.endswith("ª"):
        return (2, int(planta.removesuffix("ª")))
    return (0, int(planta))
