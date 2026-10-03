"""Tests de las opciones binarias del contrato público."""

from tasador.domain.tags import (
    ETIQUETAS_GRUPO,
    GRUPO_LEGAL,
    GRUPO_VIVIENDA,
    OPCIONES_BINARIAS,
    columnas_binarias_publicas,
)


def opciones_de_grupo(grupo):
    claves = []
    for opcion in OPCIONES_BINARIAS:
        if opcion.grupo == grupo:
            claves.append(opcion.clave)
    return claves


def test_hay_22_casillas_de_vivienda_y_9_legales():
    assert len(opciones_de_grupo(GRUPO_VIVIENDA)) == 22
    assert len(opciones_de_grupo(GRUPO_LEGAL)) == 9


def test_claves_unicas_en_snake_case():
    claves = []
    for opcion in OPCIONES_BINARIAS:
        claves.append(opcion.clave)
        assert opcion.clave.isascii()
        assert opcion.clave == opcion.clave.lower()
        assert " " not in opcion.clave
    assert len(claves) == len(set(claves))


def test_ninguna_columna_se_repite_entre_opciones():
    vistas = []
    for opcion in OPCIONES_BINARIAS:
        for columna in opcion.columnas:
            assert columna not in vistas
            vistas.append(columna)


def test_columnas_publicas_existen_en_el_modelo(modelo):
    columnas_modelo = set(modelo.regressor_.feature_names_)
    for columna in columnas_binarias_publicas():
        assert columna in columnas_modelo


def test_hay_33_columnas_publicas():
    assert len(columnas_binarias_publicas()) == 33


def test_los_siete_flags_son_publicos(modelo):
    for columna in modelo.regressor_.feature_names_:
        if columna.startswith("flag_"):
            assert columna in columnas_binarias_publicas()


def test_pares_de_sinonimos_son_una_sola_casilla():
    columnas_por_clave = {}
    for opcion in OPCIONES_BINARIAS:
        columnas_por_clave[opcion.clave] = opcion.columnas
    assert columnas_por_clave["renovated"] == ("tag_reformado", "tag_reformada")
    assert columnas_por_clave["brand_new"] == ("tag_estrenar", "tag_nuevo")


def test_tags_descartados_no_son_publicos():
    for columna in ("tag_piso", "tag_lujo", "tag_goya", "tag_interior", "tag_exterior"):
        assert columna not in columnas_binarias_publicas()


def test_todas_las_opciones_y_grupos_tienen_etiqueta_en_ambos_idiomas():
    for opcion in OPCIONES_BINARIAS:
        assert opcion.grupo in ETIQUETAS_GRUPO
        assert opcion.etiqueta.es
        assert opcion.etiqueta.en
    for etiqueta in ETIQUETAS_GRUPO.values():
        assert etiqueta.es
        assert etiqueta.en
