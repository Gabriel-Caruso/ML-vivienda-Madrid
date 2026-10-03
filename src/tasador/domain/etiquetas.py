"""Etiquetas legibles, en español e inglés, de los valores categóricos.

Las zonas y los barrios no se traducen: se muestran igual en ambos idiomas.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Etiqueta:
    """Texto visible de un elemento en cada idioma de la interfaz."""

    es: str
    en: str


def etiqueta_sin_traducir(texto: str) -> Etiqueta:
    """Etiqueta para nombres propios, que se muestran igual en ambos idiomas."""
    return Etiqueta(es=texto, en=texto)


# Valor de zona en los datos (identificador de Idealista) -> nombre oficial del distrito
NOMBRES_ZONA = {
    "arganzuela": "Arganzuela",
    "barajas": "Barajas",
    "barrio-de-salamanca": "Salamanca",
    "carabanchel": "Carabanchel",
    "centro": "Centro",
    "chamartin": "Chamartín",
    "chamberi": "Chamberí",
    "ciudad-lineal": "Ciudad Lineal",
    "fuencarral": "Fuencarral-El Pardo",
    "hortaleza": "Hortaleza",
    "latina": "Latina",
    "moncloa": "Moncloa-Aravaca",
    "moratalaz": "Moratalaz",
    "puente-de-vallecas": "Puente de Vallecas",
    "retiro": "Retiro",
    "san-blas": "San Blas-Canillejas",
    "tetuan": "Tetuán",
    "usera": "Usera",
    "vicalvaro": "Vicálvaro",
    "villa-de-vallecas": "Villa de Vallecas",
    "villaverde": "Villaverde",
}

ETIQUETAS_TIPO_INMUEBLE = {
    "Casa o chalet independiente": Etiqueta(es="Casa o chalet independiente", en="Detached house"),
    "Casa rural": Etiqueta(es="Casa rural", en="Country house"),
    "Chalet": Etiqueta(es="Chalet", en="Chalet"),
    "Chalet adosado": Etiqueta(es="Chalet adosado", en="Terraced house"),
    "Chalet pareado": Etiqueta(es="Chalet pareado", en="Semi-detached house"),
    "Dúplex": Etiqueta(es="Dúplex", en="Duplex"),
    "Estudio": Etiqueta(es="Estudio", en="Studio"),
    "Piso": Etiqueta(es="Piso", en="Flat"),
    "Ático": Etiqueta(es="Ático", en="Penthouse"),
}

ETIQUETAS_ASCENSOR = {
    "S": Etiqueta(es="Sí", en="Yes"),
    "N": Etiqueta(es="No", en="No"),
}

ETIQUETAS_LOCALIZACION = {
    "EXTERIOR": Etiqueta(es="Exterior", en="Exterior"),
    "INTERIOR": Etiqueta(es="Interior", en="Interior"),
}

ETIQUETAS_PLANTA_ESPECIAL = {
    "BAJO": Etiqueta(es="Bajo", en="Ground floor"),
    "ENTREPLANTA": Etiqueta(es="Entreplanta", en="Mezzanine"),
}


def sufijo_ordinal_ingles(numero: int) -> str:
    """Sufijo ordinal en inglés: 1st, 2nd, 3rd, 4th, 11th, 12th, 13th, 21st..."""
    if 11 <= numero % 100 <= 13:
        return "th"
    if numero % 10 == 1:
        return "st"
    if numero % 10 == 2:
        return "nd"
    if numero % 10 == 3:
        return "rd"
    return "th"


def etiqueta_planta(planta: str) -> Etiqueta:
    """Etiqueta de una planta del catálogo.

    Formatos en los datos: "BAJO", "ENTREPLANTA", ordinales como "3ª" y
    sótanos como "-1" (en el preprocesado, "SÓTANO" se convirtió en "-1").
    """
    if planta in ETIQUETAS_PLANTA_ESPECIAL:
        return ETIQUETAS_PLANTA_ESPECIAL[planta]
    if planta.endswith("ª"):
        numero = int(planta.removesuffix("ª"))
        return Etiqueta(es=f"{numero}ª planta", en=f"{numero}{sufijo_ordinal_ingles(numero)} floor")
    numero = int(planta)
    if numero >= 0:
        raise ValueError(f"Formato de planta no reconocido: {planta!r}")
    return Etiqueta(es=f"Sótano ({numero})", en=f"Basement ({numero})")
