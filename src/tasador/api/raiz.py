"""Raíz del sitio: sirve la interfaz web estática de src/tasador/web/.

Los mismos archivos se publican en producción como Static Site de Render; aquí
la app los sirve para trabajar en local con un solo comando.

Cada carpeta de web/ se monta en su propia ruta (/css, /js, /datos...) y cada
archivo de la raíz tiene su ruta (/config.js...). No se monta un StaticFiles
sobre "/" porque capturaría también las rutas de la API: un DELETE a
/api/v1/predict acabaría en los archivos estáticos en lugar de dar 405.

Todos los archivos se sirven con "Cache-Control: no-cache": el navegador puede
guardarlos, pero los revalida (ETag) en cada carga. Así un JavaScript o unos
datos regenerados nunca se quedan atrasados en caché.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from tasador.config import RUTA_WEB

ARCHIVO_INDICE = "index.html"
METODOS_LECTURA = ["GET", "HEAD"]
CABECERAS_SIN_CACHE = {"Cache-Control": "no-cache"}


class ArchivosQueSeRevalidan(StaticFiles):
    """StaticFiles que añade Cache-Control: no-cache a cada archivo."""

    def file_response(self, *args, **kwargs):
        respuesta = super().file_response(*args, **kwargs)
        respuesta.headers.update(CABECERAS_SIN_CACHE)
        return respuesta


def respuesta_de_archivo(ruta: Path):
    """Endpoint que devuelve siempre el mismo archivo (GET y HEAD)."""

    def servir_archivo() -> FileResponse:
        return FileResponse(ruta, headers=CABECERAS_SIN_CACHE)

    return servir_archivo


def registrar_web(app: FastAPI, ruta_web: Path = RUTA_WEB) -> None:
    """Publica index.html en "/" y el resto de archivos y carpetas de la web."""
    app.add_api_route(
        "/",
        respuesta_de_archivo(ruta_web / ARCHIVO_INDICE),
        methods=METODOS_LECTURA,
        include_in_schema=False,
    )
    for elemento in sorted(ruta_web.iterdir()):
        if elemento.is_dir():
            app.mount(
                f"/{elemento.name}",
                ArchivosQueSeRevalidan(directory=elemento),
                name=f"web-{elemento.name}",
            )
        elif elemento.name != ARCHIVO_INDICE:
            app.add_api_route(
                f"/{elemento.name}",
                respuesta_de_archivo(elemento),
                methods=METODOS_LECTURA,
                include_in_schema=False,
            )
