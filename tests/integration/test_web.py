"""La app sirve la interfaz web en "/" y aplica CORS solo a los orígenes configurados."""

import pytest
from fastapi.testclient import TestClient

from tasador.config import RUTA_WEB, leer_origenes_permitidos, origenes_desde_entorno
from tasador.main import create_app

ORIGEN_PERMITIDO = "https://ml-vivienda-madrid-1.onrender.com"
ORIGEN_AJENO = "https://otro-sitio.example"

# Web


def test_raiz_sirve_la_pagina(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert '<html lang="es">' in respuesta.text
    assert 'src="js/app.js"' in respuesta.text


def test_head_en_la_raiz_sigue_respondiendo(cliente):
    respuesta = cliente.head("/")
    assert respuesta.status_code == 200
    assert respuesta.content == b""


@pytest.mark.parametrize(
    "ruta",
    [
        "/config.js",
        "/css/estilo.css",
        "/js/app.js",
        "/js/formulario.js",
        "/i18n/es.json",
        "/i18n/en.json",
        "/datos/catalogo.json",
        "/datos/informe_modelo.json",
        "/datos/arbol.json",
    ],
)
def test_archivos_de_la_web_accesibles(cliente, ruta):
    assert cliente.get(ruta).status_code == 200


def test_config_por_defecto_usa_el_mismo_origen(cliente):
    texto = cliente.get("/config.js").text
    assert 'apiBaseUrl: ""' in texto
    assert 'portfolioUrl: ""' in texto


def test_la_web_no_tapa_las_rutas_de_la_api(cliente):
    assert cliente.get("/api/v1/health").json()["model_loaded"] is True
    assert cliente.delete("/api/v1/predict").status_code == 405
    assert cliente.get("/no-existe").json()["errors"][0]["code"] == "NOT_FOUND"


def test_cada_archivo_de_la_raiz_web_se_publica(cliente):
    for elemento in RUTA_WEB.iterdir():
        if elemento.is_file() and elemento.name != "index.html":
            assert cliente.get(f"/{elemento.name}").status_code == 200


# CORS


@pytest.fixture(scope="module")
def cliente_con_cors():
    app = create_app(origenes_permitidos=[ORIGEN_PERMITIDO])
    with TestClient(app) as cliente_http:
        yield cliente_http


def preflight(cliente, origen):
    return cliente.options(
        "/api/v1/predict",
        headers={
            "Origin": origen,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )


def test_cors_acepta_el_origen_configurado(cliente_con_cors):
    respuesta = preflight(cliente_con_cors, ORIGEN_PERMITIDO)
    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == ORIGEN_PERMITIDO


def test_cors_rechaza_otros_origenes(cliente_con_cors):
    respuesta = preflight(cliente_con_cors, ORIGEN_AJENO)
    assert respuesta.status_code == 400
    assert "access-control-allow-origin" not in respuesta.headers


def test_cors_en_peticion_real_solo_para_el_origen_configurado(cliente_con_cors):
    permitida = cliente_con_cors.get("/api/v1/health", headers={"Origin": ORIGEN_PERMITIDO})
    ajena = cliente_con_cors.get("/api/v1/health", headers={"Origin": ORIGEN_AJENO})
    assert permitida.headers["access-control-allow-origin"] == ORIGEN_PERMITIDO
    assert "access-control-allow-origin" not in ajena.headers


def test_sin_origenes_configurados_no_se_admite_ninguno(cliente):
    respuesta = preflight(cliente, ORIGEN_PERMITIDO)
    assert "access-control-allow-origin" not in respuesta.headers


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("", []),
        ("https://a.com", ["https://a.com"]),
        (" https://a.com/ , https://b.com,, ", ["https://a.com", "https://b.com"]),
    ],
)
def test_leer_origenes_permitidos(valor, esperado):
    assert leer_origenes_permitidos(valor) == esperado


def test_origenes_desde_la_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("ALLOWED_ORIGINS", f"{ORIGEN_PERMITIDO},https://b.com")
    assert origenes_desde_entorno() == [ORIGEN_PERMITIDO, "https://b.com"]
    monkeypatch.delenv("ALLOWED_ORIGINS")
    assert origenes_desde_entorno() == []


@pytest.mark.parametrize("ruta", ["/", "/config.js", "/js/app.js", "/datos/informe_modelo.json"])
def test_archivos_de_la_web_se_revalidan_siempre(cliente, ruta):
    assert cliente.get(ruta).headers["cache-control"] == "no-cache"


def test_la_api_no_lleva_la_cabecera_de_la_web(cliente):
    assert "cache-control" not in cliente.get("/api/v1/health").headers
