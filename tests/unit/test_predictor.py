"""Tests del servicio que convierte peticiones en filas del modelo."""

import math
from types import SimpleNamespace

import pandas as pd
import pytest

from tasador.domain.reglas import VALOR_DESCONOCIDO, VALOR_NO_APLICA
from tasador.domain.tags import OPCIONES_BINARIAS, columnas_binarias_publicas
from tasador.schemas.prediccion import PeticionPrediccion
from tasador.services.predictor import (
    ColumnasIncompatiblesError,
    Predictor,
    comprobar_columnas,
)
from tests.ayudas import fila_como_en_entrenamiento, peticion_desde_fila, peticion_valida


def peticion(**cambios) -> PeticionPrediccion:
    datos = peticion_valida()
    datos.update(cambios)
    return PeticionPrediccion.model_validate(datos)


def fila(predictor, **cambios) -> pd.Series:
    return predictor.construir_fila(peticion(**cambios)).iloc[0]


# Estructura de la fila


def test_columnas_y_orden_identicos_al_modelo(predictor, modelo):
    tabla = predictor.construir_fila(peticion())
    assert list(tabla.columns) == list(modelo.regressor_.feature_names_)
    assert len(tabla) == 1


def test_tipos_como_en_el_entrenamiento(predictor):
    tabla = predictor.construir_fila(peticion())
    assert tabla["metros"].dtype == "int64"
    assert tabla["baños_limpio"].dtype == "float64"
    assert tabla["habitaciones_limpio"].dtype == "float64"
    for columna in ("zona", "tipo_inmueble", "barrio", "planta_limpio"):
        assert pd.api.types.is_string_dtype(tabla[columna])
    for columna in tabla.columns:
        if columna.startswith(("flag_", "tag_")):
            assert tabla[columna].dtype == "int64"


def test_campos_se_mapean_a_sus_columnas(predictor):
    valores = fila(predictor)
    assert valores["metros"] == 85
    assert valores["baños_limpio"] == 2.0
    assert valores["habitaciones_limpio"] == 3.0
    assert valores["zona"] == "chamberi"
    assert valores["barrio"] == "Trafalgar"
    assert valores["tipo_inmueble"] == "Piso"
    assert valores["ascensor_limpio"] == "S"
    assert valores["localizacion_limpio"] == "EXTERIOR"
    assert valores["planta_limpio"] == "3ª"


# Nulos y reglas del preprocesado


def test_banos_y_habitaciones_nulos_pasan_a_nan(predictor):
    valores = fila(predictor, bathrooms=None, rooms=None)
    assert math.isnan(valores["baños_limpio"])
    assert math.isnan(valores["habitaciones_limpio"])


def test_estudio_sin_habitaciones_pasa_a_cero(predictor):
    valores = fila(predictor, property_type="Estudio", rooms=None)
    assert valores["habitaciones_limpio"] == 0.0


def test_cero_habitaciones_se_respeta(predictor):
    assert fila(predictor, rooms=0)["habitaciones_limpio"] == 0.0


def test_piso_sin_ascensor_localizacion_ni_planta_es_desconocido(predictor):
    valores = fila(predictor, lift=None, position=None, floor=None)
    assert valores["ascensor_limpio"] == VALOR_DESCONOCIDO
    assert valores["localizacion_limpio"] == VALOR_DESCONOCIDO
    assert valores["planta_limpio"] == VALOR_DESCONOCIDO


def test_chalet_sin_ascensor_localizacion_ni_planta_es_no_aplica(predictor):
    valores = fila(predictor, property_type="Chalet adosado", lift=None, position=None, floor=None)
    assert valores["ascensor_limpio"] == VALOR_NO_APLICA
    assert valores["localizacion_limpio"] == VALOR_NO_APLICA
    assert valores["planta_limpio"] == VALOR_NO_APLICA


# Columnas binarias


def test_tags_y_flags_no_enviados_valen_cero(predictor, modelo):
    valores = fila(predictor, options=[])
    for columna in modelo.regressor_.feature_names_:
        if columna.startswith(("flag_", "tag_")):
            assert valores[columna] == 0


def test_opciones_enviadas_valen_uno_y_el_resto_cero(predictor, modelo):
    valores = fila(predictor, options=["terrace", "squatted"])
    assert valores["tag_terraza"] == 1
    assert valores["flag_okupada"] == 1
    for columna in modelo.regressor_.feature_names_:
        if columna.startswith(("flag_", "tag_")) and columna not in ("tag_terraza", "flag_okupada"):
            assert valores[columna] == 0


def test_casilla_de_sinonimos_activa_ambas_columnas(predictor):
    valores = fila(predictor, options=["renovated", "brand_new"])
    assert valores["tag_reformado"] == 1
    assert valores["tag_reformada"] == 1
    assert valores["tag_estrenar"] == 1
    assert valores["tag_nuevo"] == 1


def test_opcion_repetida_no_cambia_la_fila(predictor):
    una = predictor.construir_fila(peticion(options=["terrace"]))
    dos = predictor.construir_fila(peticion(options=["terrace", "terrace"]))
    pd.testing.assert_frame_equal(una, dos)


def test_todas_las_opciones_a_la_vez(predictor, modelo):
    claves = []
    for opcion in OPCIONES_BINARIAS:
        claves.append(opcion.clave)
    valores = fila(predictor, options=claves)
    for columna in modelo.regressor_.feature_names_:
        if columna.startswith(("flag_", "tag_")):
            esperado = 1 if columna in columnas_binarias_publicas() else 0
            assert valores[columna] == esperado


# Equivalencia con el notebook


def test_filas_del_fixture_se_reconstruyen_exactamente(predictor, filas_referencia):
    columnas = filas_referencia["columnas"]
    for fila_fixture in filas_referencia["filas"]:
        datos = peticion_desde_fila(fila_fixture["valores"])
        construida = predictor.construir_fila(PeticionPrediccion.model_validate(datos))
        esperada = fila_como_en_entrenamiento(fila_fixture["valores"], columnas)
        pd.testing.assert_frame_equal(construida, esperada)


# Prediccion


def test_prediccion_identica_a_model_predict(predictor, modelo):
    tabla = predictor.construir_fila(peticion())
    resultado = predictor.predecir(peticion())
    assert resultado.precio == float(modelo.predict(tabla)[0])


def test_prediccion_incluye_horquilla_de_su_tramo(predictor):
    resultado = predictor.predecir(peticion())
    assert resultado.minimo == pytest.approx(resultado.precio * (1 - resultado.margen))
    assert resultado.maximo == pytest.approx(resultado.precio * (1 + resultado.margen))


# Compatibilidad entre modelo y dominio


def modelo_falso(columnas):
    return SimpleNamespace(regressor_=SimpleNamespace(feature_names_=columnas))


def test_columna_del_modelo_sin_origen_falla(modelo):
    columnas = [*modelo.regressor_.feature_names_, "columna_nueva"]
    with pytest.raises(ColumnasIncompatiblesError, match="columna_nueva"):
        comprobar_columnas(columnas)


def test_columna_del_dominio_ausente_en_el_modelo_falla(modelo):
    columnas = list(modelo.regressor_.feature_names_)
    columnas.remove("tag_terraza")
    with pytest.raises(ColumnasIncompatiblesError, match="tag_terraza"):
        Predictor(modelo_falso(columnas))


def test_campo_principal_ausente_en_el_modelo_falla(modelo):
    columnas = list(modelo.regressor_.feature_names_)
    columnas.remove("metros")
    with pytest.raises(ColumnasIncompatiblesError, match="metros"):
        Predictor(modelo_falso(columnas))


def test_modelo_real_es_compatible(modelo):
    comprobar_columnas(list(modelo.regressor_.feature_names_))
