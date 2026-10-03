"""Tests del archivo de fixtures: contenido coherente con el modelo y el contrato."""

from tasador.domain.reglas import VALOR_NO_APLICA
from tasador.domain.tags import OPCIONES_BINARIAS, columnas_binarias_publicas


def test_fixture_tiene_20_filas(filas_referencia):
    assert len(filas_referencia["filas"]) == 20


def test_columnas_del_fixture_son_las_del_modelo_en_su_orden(filas_referencia, modelo):
    assert filas_referencia["columnas"] == list(modelo.regressor_.feature_names_)
    for fila in filas_referencia["filas"]:
        assert list(fila["valores"]) == filas_referencia["columnas"]


def test_fixture_no_contiene_datos_del_anuncio(filas_referencia):
    for fila in filas_referencia["filas"]:
        for columna in ("titulo", "descripcion", "Enlace", "tags", "PrecioActual"):
            assert columna not in fila["valores"]


def test_filas_expresables_por_la_api(filas_referencia):
    publicas = columnas_binarias_publicas()
    for fila in filas_referencia["filas"]:
        valores = fila["valores"]
        for columna, valor in valores.items():
            if columna.startswith(("flag_", "tag_")) and columna not in publicas:
                assert valor == 0, f"Fila {fila['indice_test']}: {columna} activa"
        for opcion in OPCIONES_BINARIAS:
            valores_opcion = set()
            for columna in opcion.columnas:
                valores_opcion.add(valores[columna])
            assert len(valores_opcion) == 1, f"Fila {fila['indice_test']}: {opcion.clave}"


def test_valores_categoricos_en_catalogo(filas_referencia, catalogo):
    for fila in filas_referencia["filas"]:
        valores = fila["valores"]
        assert catalogo.barrio_pertenece_a_zona(valores["barrio"], valores["zona"])
        assert valores["tipo_inmueble"] in catalogo.tipos_inmueble
        assert valores["ascensor_limpio"] in catalogo.ascensor
        assert valores["localizacion_limpio"] in catalogo.localizacion
        assert valores["planta_limpio"] in catalogo.plantas


def test_banos_nunca_es_cero(filas_referencia):
    for fila in filas_referencia["filas"]:
        assert fila["valores"]["baños_limpio"] != 0


def test_cubre_variedad_de_casos(filas_referencia):
    zonas = set()
    tipos = set()
    con_banos = 0
    sin_banos = 0
    con_no_aplica = 0
    for fila in filas_referencia["filas"]:
        valores = fila["valores"]
        zonas.add(valores["zona"])
        tipos.add(valores["tipo_inmueble"])
        if valores["baños_limpio"] is None:
            sin_banos += 1
        else:
            con_banos += 1
        if valores["planta_limpio"] == VALOR_NO_APLICA:
            con_no_aplica += 1
    assert len(zonas) >= 10
    assert len(tipos) >= 5
    assert con_banos >= 3
    assert sin_banos >= 3
    assert con_no_aplica >= 1
