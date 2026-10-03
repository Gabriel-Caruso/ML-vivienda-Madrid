"""Test de referencia: la API transforma igual que el notebook.

Para cada fila del fixture, la predicción que devuelve la API a partir de la
petición equivalente debe ser idéntica (no aproximada) a model.predict()
sobre la fila ya procesada por el notebook. No evalúa el modelo: no usa el
precio real ni calcula métricas.
"""

from tests.ayudas import fila_como_en_entrenamiento, peticion_desde_fila


def test_prediccion_de_la_api_identica_a_la_del_notebook(cliente, modelo, filas_referencia):
    columnas = filas_referencia["columnas"]
    distintas = []
    for fila in filas_referencia["filas"]:
        respuesta = cliente.post("/api/v1/predict", json=peticion_desde_fila(fila["valores"]))
        assert respuesta.status_code == 200, respuesta.json()

        esperada = float(modelo.predict(fila_como_en_entrenamiento(fila["valores"], columnas))[0])
        obtenida = respuesta.json()["estimated_price"]
        if obtenida != esperada:
            distintas.append((fila["indice_test"], obtenida, esperada))
    assert distintas == []
