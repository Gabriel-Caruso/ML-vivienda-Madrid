"""Escritura estable de los JSON que generan los scripts.

Mismas entradas, mismo texto byte a byte: sangría fija, UTF-8 sin escapar,
saltos de línea LF y un salto final. Así los archivos versionados solo cambian
cuando cambian los datos.
"""

import json
from pathlib import Path


def serializar(datos: dict) -> str:
    return json.dumps(datos, ensure_ascii=False, indent=2) + "\n"


def escribir(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(serializar(datos), encoding="utf-8", newline="\n")
