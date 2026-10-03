"""Coherencia de la configuración de CI y despliegue con el código.

Comprobaciones de texto: el proyecto no incluye un parser de YAML y no
merece la pena añadir una dependencia solo para esto.
"""

import re

from tasador.config import RAIZ_PROYECTO
from tasador.main import create_app

RUTA_RENDER = RAIZ_PROYECTO / "render.yaml"
RUTA_CI = RAIZ_PROYECTO / ".github" / "workflows" / "ci.yml"
VERSION_UV = "0.12.23"


def leer(ruta) -> str:
    return ruta.read_text(encoding="utf-8")


def rutas_de_la_app() -> set[str]:
    """Rutas publicadas, según el esquema OpenAPI de la app."""
    return set(create_app().openapi()["paths"])


def test_python_fijado():
    assert leer(RAIZ_PROYECTO / ".python-version").strip() == "3.14.4"


def test_health_check_de_render_apunta_a_una_ruta_existente():
    coincidencia = re.search(r"healthCheckPath:\s*(\S+)", leer(RUTA_RENDER))
    assert coincidencia is not None
    assert coincidencia.group(1) == "/api/v1/health"
    assert coincidencia.group(1) in rutas_de_la_app()


def test_arranque_de_render_usa_la_fabrica_y_el_puerto_de_render():
    render = leer(RUTA_RENDER)
    assert "uvicorn --factory tasador.main:create_app" in render
    assert "--host 0.0.0.0" in render
    assert "--port $PORT" in render


def test_render_instala_solo_lo_bloqueado_y_sin_dev():
    assert "buildCommand: uv sync --locked --no-dev" in leer(RUTA_RENDER)


def test_render_en_plan_gratuito_y_despliegue_tras_la_ci():
    render = leer(RUTA_RENDER)
    assert "plan: free" in render
    assert "runtime: python" in render
    assert "autoDeployTrigger: checksPass" in render


def test_misma_version_de_uv_en_ci_y_render():
    assert f'version: "{VERSION_UV}"' in leer(RUTA_CI)
    assert re.search(rf"key: UV_VERSION\s+value: {re.escape(VERSION_UV)}", leer(RUTA_RENDER))


def test_ci_ejecuta_las_tres_comprobaciones_de_calidad():
    ci = leer(RUTA_CI)
    assert "uv sync --locked" in ci
    assert "uv run ruff format --check ." in ci
    assert "uv run ruff check ." in ci
    assert "uv run pytest" in ci


def test_ci_en_cada_push_y_pull_request():
    ci = leer(RUTA_CI)
    assert "push:" in ci
    assert "pull_request:" in ci
