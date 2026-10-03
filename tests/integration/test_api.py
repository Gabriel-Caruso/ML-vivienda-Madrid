"""Tests de integración de los endpoints con TestClient."""

import pytest
from fastapi.testclient import TestClient

from tasador.config import VERSION_APP
from tasador.main import create_app
from tasador.schemas.errores import CodigoError
from tests.ayudas import peticion_valida

URL_PREDICT = "/api/v1/predict"


def con(**cambios) -> dict:
    datos = peticion_valida()
    datos.update(cambios)
    return datos


def codigos(respuesta) -> list[tuple[str, str | None]]:
    resultado = []
    for error in respuesta.json()["errors"]:
        resultado.append((error["code"], error["field"]))
    return resultado


# GET /


def test_raiz(cliente):
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["version"] == VERSION_APP
    assert cuerpo["docs"] == "/docs"
    assert cuerpo["endpoints"] == {
        "health": "/api/v1/health",
        "metadata": "/api/v1/metadata",
        "predict": "/api/v1/predict",
    }


def test_swagger_disponible(cliente):
    assert cliente.get("/docs").status_code == 200
    esquema = cliente.get("/openapi.json").json()
    assert "/api/v1/predict" in esquema["paths"]


# GET /api/v1/health


def test_health_con_modelo_cargado(cliente):
    respuesta = cliente.get("/api/v1/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "model_loaded": True}


def test_health_sin_modelo_devuelve_503():
    app = create_app()
    # Sin context manager no se ejecuta el lifespan: el modelo no se carga
    cliente_sin_modelo = TestClient(app)
    respuesta = cliente_sin_modelo.get("/api/v1/health")
    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable", "model_loaded": False}


def test_predict_sin_modelo_devuelve_503():
    cliente_sin_modelo = TestClient(create_app())
    respuesta = cliente_sin_modelo.post(URL_PREDICT, json=peticion_valida())
    assert respuesta.status_code == 503
    assert codigos(respuesta) == [("MODEL_NOT_LOADED", None)]


def test_app_no_arranca_si_falta_el_modelo(tmp_path):
    app = create_app(ruta_modelo=tmp_path / "no_existe.joblib")
    with pytest.raises(FileNotFoundError), TestClient(app):
        pass


# GET /api/v1/metadata


def test_metadata(cliente):
    respuesta = cliente.get("/api/v1/metadata")
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["districts"]) == 21
    assert len(cuerpo["property_types"]) == 9
    assert len(cuerpo["option_groups"]) == 2
    centro = None
    for distrito in cuerpo["districts"]:
        if distrito["value"] == "centro":
            centro = distrito
    assert "Sol" in centro["neighbourhoods"]
    assert "Sanchinarro" not in centro["neighbourhoods"]


# POST /api/v1/predict: casos válidos


def test_predict_valido(cliente):
    respuesta = cliente.post(URL_PREDICT, json=peticion_valida())
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"estimated_price", "error_margin", "price_min", "price_max"}
    assert cuerpo["price_min"] < cuerpo["estimated_price"] < cuerpo["price_max"]
    assert cuerpo["price_min"] == pytest.approx(
        cuerpo["estimated_price"] * (1 - cuerpo["error_margin"])
    )


def test_predict_minimo(cliente):
    datos = {
        "area_m2": 40,
        "district": "centro",
        "neighbourhood": "Sol",
        "property_type": "Estudio",
    }
    assert cliente.post(URL_PREDICT, json=datos).status_code == 200


def test_predict_chalet_sin_datos_opcionales(cliente):
    datos = {
        "area_m2": 250,
        "district": "moncloa",
        "neighbourhood": "Aravaca",
        "property_type": "Chalet",
        "bathrooms": None,
        "rooms": None,
        "lift": None,
        "position": None,
        "floor": None,
    }
    assert cliente.post(URL_PREDICT, json=datos).status_code == 200


def test_predict_con_todas_las_opciones(cliente):
    metadata = cliente.get("/api/v1/metadata").json()
    claves = []
    for grupo in metadata["option_groups"]:
        for opcion in grupo["options"]:
            claves.append(opcion["key"])
    assert cliente.post(URL_PREDICT, json=con(options=claves)).status_code == 200


# POST /api/v1/predict: cada código de error


@pytest.mark.parametrize(
    ("datos", "esperado"),
    [
        (
            con(district="centro", neighbourhood="Sanchinarro"),
            ("BARRIO_NOT_IN_ZONE", "neighbourhood"),
        ),
        (con(bathrooms=0), ("BATHROOMS_ZERO", "bathrooms")),
        (con(area_m2=5), ("OUT_OF_RANGE", "area_m2")),
        (con(rooms=25), ("OUT_OF_RANGE", "rooms")),
        (con(bathrooms=9), ("OUT_OF_RANGE", "bathrooms")),
        (con(district="alcobendas"), ("VALUE_NOT_IN_CATALOG", "district")),
        (con(neighbourhood="Inventado"), ("VALUE_NOT_IN_CATALOG", "neighbourhood")),
        (con(property_type="Mansión"), ("VALUE_NOT_IN_CATALOG", "property_type")),
        (con(lift="DESCONOCIDO"), ("VALUE_NOT_IN_CATALOG", "lift")),
        (con(position="NORTE"), ("VALUE_NOT_IN_CATALOG", "position")),
        (con(floor="22ª"), ("VALUE_NOT_IN_CATALOG", "floor")),
        (con(options=["jacuzzi"]), ("UNKNOWN_OPTION", "options")),
        (con(area_m2="85"), ("INVALID_TYPE", "area_m2")),
        (con(rooms=2.5), ("INVALID_TYPE", "rooms")),
        (con(precio=100), ("UNKNOWN_FIELD", "precio")),
    ],
)
def test_predict_codigo_de_error(cliente, datos, esperado):
    respuesta = cliente.post(URL_PREDICT, json=datos)
    assert respuesta.status_code == 422
    assert codigos(respuesta) == [esperado]


def test_predict_campo_obligatorio_ausente(cliente):
    datos = peticion_valida()
    del datos["district"]
    respuesta = cliente.post(URL_PREDICT, json=datos)
    assert respuesta.status_code == 422
    assert codigos(respuesta) == [("FIELD_REQUIRED", "district")]


def test_predict_json_mal_formado(cliente):
    respuesta = cliente.post(
        URL_PREDICT, content=b"{area_m2: 85", headers={"content-type": "application/json"}
    )
    assert respuesta.status_code == 422
    assert codigos(respuesta)[0][0] == "INVALID_JSON"


def test_predict_sin_cuerpo(cliente):
    respuesta = cliente.post(URL_PREDICT)
    assert respuesta.status_code == 422
    assert codigos(respuesta)[0][0] == "FIELD_REQUIRED"


def test_predict_varios_errores_a_la_vez(cliente):
    respuesta = cliente.post(URL_PREDICT, json=con(area_m2=1, bathrooms=0))
    assert respuesta.status_code == 422
    assert set(codigos(respuesta)) == {("OUT_OF_RANGE", "area_m2"), ("BATHROOMS_ZERO", "bathrooms")}


def test_respuesta_de_error_tiene_forma_estable(cliente):
    error = cliente.post(URL_PREDICT, json=con(bathrooms=8)).json()["errors"][0]
    assert set(error) == {"code", "field", "message", "params"}
    assert error["params"] == {"min": 1, "max": 7}


def test_barrio_de_otra_zona_informa_de_ambos(cliente):
    respuesta = cliente.post(URL_PREDICT, json=con(district="centro", neighbourhood="Sanchinarro"))
    assert respuesta.json()["errors"][0]["params"] == {
        "neighbourhood": "Sanchinarro",
        "district": "centro",
    }


def test_error_interno_devuelve_codigo_estable(monkeypatch):
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as cliente_propio:

        def fallar(peticion):
            raise RuntimeError("fallo simulado")

        monkeypatch.setattr(app.state.predictor, "predecir", fallar)
        respuesta = cliente_propio.post(URL_PREDICT, json=peticion_valida())
    assert respuesta.status_code == 500
    assert codigos(respuesta) == [("INTERNAL_ERROR", None)]


def test_todos_los_codigos_de_validacion_estan_cubiertos():
    # Recordatorio: si se añade un código nuevo, debe tener su test de integración
    cubiertos = {
        "INVALID_JSON",
        "FIELD_REQUIRED",
        "UNKNOWN_FIELD",
        "INVALID_TYPE",
        "OUT_OF_RANGE",
        "BATHROOMS_ZERO",
        "VALUE_NOT_IN_CATALOG",
        "BARRIO_NOT_IN_ZONE",
        "UNKNOWN_OPTION",
        "MODEL_NOT_LOADED",
        "INTERNAL_ERROR",
    }
    # INVALID_VALUE es el código genérico para errores de Pydantic sin código propio
    todos = set()
    for codigo in CodigoError:
        todos.add(codigo.value)
    assert todos - cubiertos == {"INVALID_VALUE"}
