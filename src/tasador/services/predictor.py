"""De una petición validada a la predicción del modelo.

Construye la fila con las columnas, el orden y los tipos exactos de
model.regressor_.feature_names_, aplicando las reglas del preprocesado
original. Si el modelo y el dominio no encajan columna a columna, falla al
crearse el predictor, no en mitad de una petición.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from tasador.domain.campos import (
    CAMPO_ASCENSOR,
    CAMPO_BANOS,
    CAMPO_BARRIO,
    CAMPO_HABITACIONES,
    CAMPO_LOCALIZACION,
    CAMPO_METROS,
    CAMPO_PLANTA,
    CAMPO_TIPO,
    CAMPO_ZONA,
    CAMPOS,
)
from tasador.domain.reglas import completar_habitaciones, valor_sin_dato
from tasador.domain.tags import OPCIONES_BINARIAS, columnas_binarias_publicas
from tasador.schemas.prediccion import PeticionPrediccion
from tasador.services.horquilla import calcular_horquilla

logger = logging.getLogger(__name__)

PREFIJOS_BINARIOS = ("flag_", "tag_")

# Tipos con los que el modelo vio cada columna al entrenar (lectura del CSV con pandas)
COLUMNAS_ENTERAS = (CAMPO_METROS.columna,)
COLUMNAS_DECIMALES = (CAMPO_BANOS.columna, CAMPO_HABITACIONES.columna)


class ColumnasIncompatiblesError(Exception):
    """El modelo y el dominio no describen las mismas columnas."""


@dataclass(frozen=True)
class Prediccion:
    """Resultado de una predicción con su horquilla, en euros enteros."""

    precio: int
    margen: float
    minimo: int
    maximo: int


def comprobar_columnas(columnas_modelo: list[str]) -> None:
    """Falla si alguna columna del modelo no tiene origen o el dominio usa una inexistente."""
    columnas_campos = set()
    for campo in CAMPOS:
        columnas_campos.add(campo.columna)

    sin_origen = []
    for columna in columnas_modelo:
        es_binaria = columna.startswith(PREFIJOS_BINARIOS)
        if columna not in columnas_campos and not es_binaria:
            sin_origen.append(columna)
    if sin_origen:
        raise ColumnasIncompatiblesError(f"Columnas del modelo sin origen: {sin_origen}")

    inexistentes = []
    for columna in sorted(columnas_campos | columnas_binarias_publicas()):
        if columna not in columnas_modelo:
            inexistentes.append(columna)
    if inexistentes:
        raise ColumnasIncompatiblesError(
            f"Columnas del dominio que el modelo no tiene: {inexistentes}"
        )


def a_decimal(valor: int | None) -> float:
    """Entero opcional a float; el dato desconocido pasa a NaN."""
    if valor is None:
        return np.nan
    return float(valor)


class Predictor:
    """Envuelve el modelo y traduce peticiones públicas a filas del modelo."""

    def __init__(self, modelo) -> None:
        self._modelo = modelo
        self._columnas = list(modelo.regressor_.feature_names_)
        comprobar_columnas(self._columnas)

    @classmethod
    def desde_archivo(cls, ruta: Path) -> Predictor:
        modelo = joblib.load(ruta)
        predictor = cls(modelo)
        logger.info("Modelo cargado desde %s (%d columnas)", ruta, len(predictor.columnas))
        return predictor

    @property
    def columnas(self) -> list[str]:
        return list(self._columnas)

    def construir_valores(self, peticion: PeticionPrediccion) -> dict:
        """Valor de cada columna del modelo para la petición."""
        tipo = peticion.property_type
        valores = {
            CAMPO_METROS.columna: peticion.area_m2,
            CAMPO_BANOS.columna: a_decimal(peticion.bathrooms),
            CAMPO_HABITACIONES.columna: a_decimal(completar_habitaciones(tipo, peticion.rooms)),
            CAMPO_ZONA.columna: peticion.district,
            CAMPO_TIPO.columna: tipo,
            CAMPO_BARRIO.columna: peticion.neighbourhood,
        }

        opcionales = (
            (CAMPO_ASCENSOR.columna, peticion.lift),
            (CAMPO_LOCALIZACION.columna, peticion.position),
            (CAMPO_PLANTA.columna, peticion.floor),
        )
        for columna, valor in opcionales:
            if valor is None:
                valores[columna] = valor_sin_dato(tipo)
            else:
                valores[columna] = valor

        # Todas las columnas binarias empiezan a 0, de forma explícita
        for columna in self._columnas:
            if columna.startswith(PREFIJOS_BINARIOS):
                valores[columna] = 0
        for opcion in OPCIONES_BINARIAS:
            if opcion.clave in peticion.options:
                for columna in opcion.columnas:
                    valores[columna] = 1
        return valores

    def construir_fila(self, peticion: PeticionPrediccion) -> pd.DataFrame:
        """DataFrame de una fila con las columnas, el orden y los tipos del modelo."""
        valores = self.construir_valores(peticion)

        faltan = []
        for columna in self._columnas:
            if columna not in valores:
                faltan.append(columna)
        if faltan:
            raise ColumnasIncompatiblesError(f"Columnas del modelo sin valor: {faltan}")

        fila = {}
        for columna in self._columnas:
            fila[columna] = [valores[columna]]
        tabla = pd.DataFrame(fila, columns=self._columnas)

        tipos = {}
        for columna in self._columnas:
            if columna in COLUMNAS_ENTERAS or columna.startswith(PREFIJOS_BINARIOS):
                tipos[columna] = "int64"
            elif columna in COLUMNAS_DECIMALES:
                tipos[columna] = "float64"
            else:
                tipos[columna] = "str"
        return tabla.astype(tipos)

    def predecir_precio(self, peticion: PeticionPrediccion) -> float:
        """Salida exacta del modelo en euros (predict() ya deshace el logaritmo)."""
        fila = self.construir_fila(peticion)
        return float(self._modelo.predict(fila)[0])

    def predecir(self, peticion: PeticionPrediccion) -> Prediccion:
        """Precio estimado y horquilla, redondeados a euros enteros.

        El tramo de error se elige con el precio ya redondeado, que es el que
        ve el usuario, y los extremos se calculan sobre ese mismo precio.
        """
        precio = round(self.predecir_precio(peticion))
        horquilla = calcular_horquilla(precio)
        return Prediccion(
            precio=precio,
            margen=horquilla.margen,
            minimo=round(horquilla.minimo),
            maximo=round(horquilla.maximo),
        )
