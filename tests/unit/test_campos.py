"""Tests de la correspondencia entre campos públicos y columnas del modelo."""

from tasador.domain.campos import CAMPOS
from tasador.domain.tags import OPCIONES_BINARIAS, columnas_binarias_publicas


def test_campos_cubren_las_9_columnas_no_binarias_del_modelo(modelo):
    columnas_campos = []
    for campo in CAMPOS:
        columnas_campos.append(campo.columna)
    assert columnas_campos == list(modelo.regressor_.feature_names_)[:9]


def test_nombres_publicos_unicos_en_ingles_y_snake_case():
    nombres = []
    for campo in CAMPOS:
        nombres.append(campo.nombre)
        assert campo.nombre.isascii()
        assert campo.nombre == campo.nombre.lower()
    for opcion in OPCIONES_BINARIAS:
        nombres.append(opcion.clave)
    assert len(nombres) == len(set(nombres))


def test_campos_tienen_etiqueta_en_ambos_idiomas():
    for campo in CAMPOS:
        assert campo.etiqueta.es
        assert campo.etiqueta.en


def test_campo_banos_se_muestra_como_banos():
    etiquetas = {}
    for campo in CAMPOS:
        etiquetas[campo.columna] = campo.etiqueta
    assert etiquetas["baños_limpio"].es == "Baños"
    assert etiquetas["baños_limpio"].en == "Bathrooms"


def test_toda_columna_del_modelo_tiene_campo_opcion_o_es_tag_descartado(modelo):
    columnas_campos = set()
    for campo in CAMPOS:
        columnas_campos.add(campo.columna)
    publicas = columnas_binarias_publicas()
    for columna in modelo.regressor_.feature_names_:
        cubierta = columna in columnas_campos or columna in publicas
        assert cubierta or columna.startswith("tag_")
