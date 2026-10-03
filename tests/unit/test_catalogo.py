"""Tests del catálogo de valores categóricos."""

import pytest

from tasador.domain.catalogo import clave_orden_alfabetico, clave_orden_planta
from tasador.domain.reglas import VALOR_DESCONOCIDO, VALOR_NO_APLICA


def test_catalogo_tiene_21_zonas_y_139_barrios(catalogo):
    assert len(catalogo.zonas) == 21
    total_barrios = 0
    for barrios in catalogo.barrios_por_zona.values():
        total_barrios += len(barrios)
    assert total_barrios == 139


def test_cada_barrio_pertenece_a_una_sola_zona(catalogo):
    zona_de_barrio = {}
    for zona, barrios in catalogo.barrios_por_zona.items():
        for barrio in barrios:
            assert barrio not in zona_de_barrio, (
                f"{barrio} en {zona_de_barrio.get(barrio)} y {zona}"
            )
            zona_de_barrio[barrio] = zona


def test_barrio_de_su_zona_es_valido(catalogo):
    assert catalogo.barrio_pertenece_a_zona("Sanchinarro", "hortaleza")
    assert catalogo.barrio_pertenece_a_zona("Malasaña-Universidad", "centro")


def test_barrio_de_otra_zona_no_es_valido(catalogo):
    assert not catalogo.barrio_pertenece_a_zona("Sanchinarro", "centro")


def test_zona_inexistente_no_tiene_barrios(catalogo):
    assert not catalogo.barrio_pertenece_a_zona("Sanchinarro", "san-sebastian-de-los-reyes")


def test_catalogo_contiene_valores_sin_dato(catalogo):
    for valores in (catalogo.ascensor, catalogo.localizacion, catalogo.plantas):
        assert VALOR_DESCONOCIDO in valores
        assert VALOR_NO_APLICA in valores


def test_tipos_de_inmueble_del_entrenamiento(catalogo):
    assert len(catalogo.tipos_inmueble) == 9
    assert "Piso" in catalogo.tipos_inmueble
    assert "Estudio" in catalogo.tipos_inmueble


def test_plantas_ordenadas_de_abajo_arriba(catalogo):
    plantas = list(catalogo.plantas)
    assert plantas[:4] == ["-2", "-1", "BAJO", "ENTREPLANTA"]
    assert plantas[-2:] == [VALOR_DESCONOCIDO, VALOR_NO_APLICA]
    assert plantas == sorted(plantas, key=clave_orden_planta)


def test_planta_22_no_esta_en_catalogo(catalogo):
    # Solo aparece en test.csv: el catálogo se construye únicamente con train
    assert "22ª" not in catalogo.plantas


def test_barrios_ordenados_ignorando_tildes(catalogo):
    barrios_latina = list(catalogo.barrios_por_zona["latina"])
    assert barrios_latina == sorted(barrios_latina, key=clave_orden_alfabetico)
    assert barrios_latina.index("Águilas") < barrios_latina.index("Campamento")


@pytest.mark.parametrize(
    ("texto_a", "texto_b"),
    [("Águilas", "Aluche"), ("Ático", "Casa rural"), ("chamartin", "Chamberí")],
)
def test_clave_orden_alfabetico_ignora_tildes_y_mayusculas(texto_a, texto_b):
    assert clave_orden_alfabetico(texto_a) < clave_orden_alfabetico(texto_b)


def test_clave_orden_planta_rechaza_formato_desconocido():
    with pytest.raises(ValueError):
        clave_orden_planta("PRIMERA")
