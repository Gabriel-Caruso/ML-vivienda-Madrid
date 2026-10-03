"""Tests de los logs técnicos."""

import logging

from tasador.config import RUTA_MODELO
from tasador.main import NOMBRE_LOGGER, configurar_logs
from tasador.services.predictor import Predictor


def test_configurar_logs_es_idempotente():
    configurar_logs()
    configurar_logs()
    logger = logging.getLogger(NOMBRE_LOGGER)
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1


def test_carga_del_modelo_queda_registrada(caplog):
    with caplog.at_level(logging.INFO, logger=NOMBRE_LOGGER):
        Predictor.desde_archivo(RUTA_MODELO)
    assert "Modelo cargado" in caplog.text
    assert "69 columnas" in caplog.text


def test_peticiones_no_se_registran(cliente, caplog):
    with caplog.at_level(logging.DEBUG, logger=NOMBRE_LOGGER):
        cliente.post(
            "/api/v1/predict",
            json={
                "area_m2": 77,
                "district": "centro",
                "neighbourhood": "Sol",
                "property_type": "Piso",
            },
        )
    assert "77" not in caplog.text
    assert "Sol" not in caplog.text
