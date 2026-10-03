"""Reglas del preprocesado original que la API debe reproducir.

Proceden del notebook 01_preprocessing.ipynb del proyecto de entrenamiento.
"""

VALOR_DESCONOCIDO = "DESCONOCIDO"
VALOR_NO_APLICA = "NO_APLICA"
VALORES_SIN_DATO = (VALOR_DESCONOCIDO, VALOR_NO_APLICA)

# En casas y chalets no tiene sentido hablar de ascensor, planta ni exterior/interior
TIPOS_CASA_O_CHALET = frozenset(
    {
        "Casa o chalet independiente",
        "Chalet adosado",
        "Chalet pareado",
        "Chalet",
        "Casa rural",
    }
)

TIPO_ESTUDIO = "Estudio"


def valor_sin_dato(tipo_inmueble: str) -> str:
    """Valor que recibe ascensor, localización o planta cuando no se indica.

    En el entrenamiento, el dato ausente se convirtió en NO_APLICA para casas
    y chalets y en DESCONOCIDO para el resto de tipos.
    """
    if tipo_inmueble in TIPOS_CASA_O_CHALET:
        return VALOR_NO_APLICA
    return VALOR_DESCONOCIDO


def completar_habitaciones(tipo_inmueble: str, habitaciones: int | None) -> int | None:
    """Habitaciones tal como las vio el modelo.

    En el entrenamiento, un estudio sin dato de habitaciones pasó a tener 0.
    En cualquier otro caso el dato ausente se mantiene como desconocido.
    """
    if habitaciones is None and tipo_inmueble == TIPO_ESTUDIO:
        return 0
    return habitaciones
