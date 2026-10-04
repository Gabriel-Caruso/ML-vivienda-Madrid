"""Genera la imagen para compartir (Open Graph) en src/tasador/web/og.png.

1200 x 630 px con la estética de la web: paleta VGA, fuente IBM VGA 9x16 y el
logo en bloques. Los tamaños de letra son múltiplos de 16 px para que la fuente
de píxeles salga nítida. Usa Pillow, que ya está en el entorno como dependencia
de matplotlib (a su vez de catboost); no se añade al proyecto.

Uso: uv run python scripts/build_og_image.py
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tasador.config import RUTA_WEB

RUTA_IMAGEN = RUTA_WEB / "og.png"
RUTA_FUENTE = RUTA_WEB / "fuentes" / "WebPlus_IBM_VGA_9x16.woff"

ANCHO = 1200
ALTO = 630
MARGEN = 24

# Paleta VGA (D-039)
NEGRO = "#000000"
GRIS = "#555555"
TEXTO = "#aaaaaa"
AMARILLO = "#ffff55"
VERDE = "#55ff55"
CIAN = "#55ffff"

LOGO = (
    "█████  ███   ████  ███  ████   ███  ████",
    "  █   █   █ █     █   █ █   █ █   █ █   █",
    "  █   █████  ███  █████ █   █ █   █ ████",
    "  █   █   █     █ █   █ █   █ █   █ █  █",
    "  █   █   █ ████  █   █ ████   ███  █   █",
)
TITULO = "tasador-madrid"
SUBTITULO = (
    "Estimación orientativa del precio de venta",
    "de una vivienda en Madrid",
)
URL = "ml-vivienda-madrid-1.onrender.com"


def texto_centrado(dibujo: ImageDraw.ImageDraw, y: int, texto: str, fuente, color: str) -> None:
    ancho_texto = dibujo.textlength(texto, font=fuente)
    dibujo.text(((ANCHO - ancho_texto) / 2, y), texto, font=fuente, fill=color)


def construir_imagen(ruta_fuente: Path) -> Image.Image:
    imagen = Image.new("RGB", (ANCHO, ALTO), NEGRO)
    dibujo = ImageDraw.Draw(imagen)
    fuente = ImageFont.truetype(str(ruta_fuente), 32)

    # Marco y barra de título sólida, como los paneles destacados de la web
    dibujo.rectangle((MARGEN, MARGEN, ANCHO - MARGEN - 1, ALTO - MARGEN - 1), outline=GRIS)
    dibujo.rectangle((MARGEN, MARGEN, ANCHO - MARGEN - 1, MARGEN + 40), fill=AMARILLO)
    texto_centrado(dibujo, MARGEN + 4, TITULO, fuente, NEGRO)

    # Logo en bloques: cada fila mide lo mismo que el tamaño de la fuente
    ancho_logo = 0
    for fila in LOGO:
        ancho_logo = max(ancho_logo, dibujo.textlength(fila, font=fuente))
    x_logo = (ANCHO - ancho_logo) / 2
    y = 130
    for fila in LOGO:
        dibujo.text((x_logo, y), fila, font=fuente, fill=AMARILLO)
        y += 32

    y += 48
    for linea in SUBTITULO:
        texto_centrado(dibujo, y, linea, fuente, TEXTO)
        y += 40

    # Línea de comando con la URL: prompt en verde, dirección en cian
    y += 40
    prompt = "$ "
    ancho_total = dibujo.textlength(prompt + URL, font=fuente)
    x = (ANCHO - ancho_total) / 2
    dibujo.text((x, y), prompt, font=fuente, fill=VERDE)
    dibujo.text((x + dibujo.textlength(prompt, font=fuente), y), URL, font=fuente, fill=CIAN)
    return imagen


def main() -> int:
    imagen = construir_imagen(RUTA_FUENTE)
    imagen.save(RUTA_IMAGEN, format="PNG", optimize=True)
    print(f"Imagen escrita en {RUTA_IMAGEN} ({ANCHO}x{ALTO})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
