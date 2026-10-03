"""Test de referencia: la API transforma igual que el notebook.

Para cada fila del fixture, a partir de su petición equivalente:
- el precio exacto que calcula el servicio es idéntico (no aproximado) a
  model.predict() sobre la fila ya procesada por el notebook;
- el precio que devuelve la API es exactamente ese valor redondeado a euros.

No evalúa el modelo: no usa el precio real ni calcula métricas.
"""

from tasador.schemas.prediccion import PeticionPrediccion
from tests.ayudas import fila_como_en_entrenamiento, peticion_desde_fila


def test_precio_exacto_identico_al_del_notebook(predictor, modelo, filas_referencia):
    columnas = filas_referencia["columnas"]
    distintas = []
    for fila in filas_referencia["filas"]:
        peticion = PeticionPrediccion.model_validate(peticion_desde_fila(fila["valores"]))
        esperado = float(modelo.predict(fila_como_en_entrenamiento(fila["valores"], columnas))[0])
        obtenido = predictor.predecir_precio(peticion)
        if obtenido != esperado:
            distintas.append((fila["indice_test"], obtenido, esperado))
    assert distintas == []


def test_api_devuelve_el_precio_del_notebook_redondeado(cliente, modelo, filas_referencia):
    columnas = filas_referencia["columnas"]
    distintas = []
    for fila in filas_referencia["filas"]:
        respuesta = cliente.post("/api/v1/predict", json=peticion_desde_fila(fila["valores"]))
        assert respuesta.status_code == 200, respuesta.json()

        esperado = round(
            float(modelo.predict(fila_como_en_entrenamiento(fila["valores"], columnas))[0])
        )
        obtenido = respuesta.json()["estimated_price"]
        if obtenido != esperado:
            distintas.append((fila["indice_test"], obtenido, esperado))
    assert distintas == []
