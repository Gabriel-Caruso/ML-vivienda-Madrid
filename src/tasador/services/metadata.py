"""Construye la metadata del formulario a partir del dominio."""

from functools import cache

from tasador.domain.campos import (
    CAMPO_BANOS,
    CAMPO_BARRIO,
    CAMPO_HABITACIONES,
    CAMPO_METROS,
    CAMPO_TIPO,
    CAMPO_ZONA,
    CAMPOS,
)
from tasador.domain.catalogo import (
    cargar_catalogo,
    clave_orden_alfabetico,
    valores_seleccionables,
)
from tasador.domain.etiquetas import (
    ETIQUETAS_ASCENSOR,
    ETIQUETAS_LOCALIZACION,
    ETIQUETAS_TIPO_INMUEBLE,
    NOMBRES_ZONA,
    Etiqueta,
    etiqueta_planta,
)
from tasador.domain.rangos import RANGO_BANOS, RANGO_HABITACIONES, RANGO_METROS, Rango
from tasador.domain.reglas import TIPOS_CASA_O_CHALET
from tasador.domain.tags import ETIQUETAS_GRUPO, OPCIONES_BINARIAS
from tasador.schemas.metadata import (
    Campo,
    Distrito,
    EtiquetaBilingue,
    GrupoOpciones,
    Opcion,
    OpcionBinaria,
    RangoNumerico,
    RespuestaMetadata,
    TipoInmueble,
)

CAMPOS_OBLIGATORIOS = (CAMPO_METROS, CAMPO_ZONA, CAMPO_BARRIO, CAMPO_TIPO)
RANGOS_POR_CAMPO = {
    CAMPO_METROS.nombre: RANGO_METROS,
    CAMPO_BANOS.nombre: RANGO_BANOS,
    CAMPO_HABITACIONES.nombre: RANGO_HABITACIONES,
}


def a_etiqueta(etiqueta: Etiqueta) -> EtiquetaBilingue:
    return EtiquetaBilingue(es=etiqueta.es, en=etiqueta.en)


def a_rango(rango: Rango | None) -> RangoNumerico | None:
    if rango is None:
        return None
    return RangoNumerico(min=rango.minimo, max=rango.maximo)


def construir_campos() -> list[Campo]:
    campos = []
    for campo in CAMPOS:
        campos.append(
            Campo(
                name=campo.nombre,
                label=a_etiqueta(campo.etiqueta),
                required=campo in CAMPOS_OBLIGATORIOS,
                range=a_rango(RANGOS_POR_CAMPO.get(campo.nombre)),
            )
        )
    return campos


def construir_distritos() -> list[Distrito]:
    catalogo = cargar_catalogo()
    distritos = []
    for zona, barrios in catalogo.barrios_por_zona.items():
        nombre = NOMBRES_ZONA[zona]
        distritos.append(
            Distrito(
                value=zona,
                label=EtiquetaBilingue(es=nombre, en=nombre),
                neighbourhoods=list(barrios),
            )
        )
    distritos.sort(key=clave_orden_distrito)
    return distritos


def clave_orden_distrito(distrito: Distrito) -> tuple[str, str]:
    """Los distritos se ordenan por su nombre visible, no por el identificador."""
    return clave_orden_alfabetico(distrito.label.es)


def construir_opciones(valores: tuple[str, ...], etiquetas: dict[str, Etiqueta]) -> list[Opcion]:
    opciones = []
    for valor in valores:
        opciones.append(Opcion(value=valor, label=a_etiqueta(etiquetas[valor])))
    return opciones


def construir_tipos_inmueble(tipos: tuple[str, ...]) -> list[TipoInmueble]:
    """Tipos con su etiqueta y si son casa o chalet (regla del preprocesado)."""
    resultado = []
    for tipo in tipos:
        resultado.append(
            TipoInmueble(
                value=tipo,
                label=a_etiqueta(ETIQUETAS_TIPO_INMUEBLE[tipo]),
                is_house=tipo in TIPOS_CASA_O_CHALET,
            )
        )
    return resultado


def construir_plantas(plantas: tuple[str, ...]) -> list[Opcion]:
    opciones = []
    for planta in valores_seleccionables(plantas):
        opciones.append(Opcion(value=planta, label=a_etiqueta(etiqueta_planta(planta))))
    return opciones


def construir_grupos() -> list[GrupoOpciones]:
    grupos = []
    for clave_grupo, etiqueta_grupo in ETIQUETAS_GRUPO.items():
        opciones = []
        for opcion in OPCIONES_BINARIAS:
            if opcion.grupo == clave_grupo:
                opciones.append(OpcionBinaria(key=opcion.clave, label=a_etiqueta(opcion.etiqueta)))
        grupos.append(
            GrupoOpciones(key=clave_grupo, label=a_etiqueta(etiqueta_grupo), options=opciones)
        )
    return grupos


@cache
def construir_metadata() -> RespuestaMetadata:
    """Metadata completa. Es estática, así que se construye una sola vez."""
    catalogo = cargar_catalogo()
    return RespuestaMetadata(
        fields=construir_campos(),
        districts=construir_distritos(),
        property_types=construir_tipos_inmueble(catalogo.tipos_inmueble),
        lift=construir_opciones(valores_seleccionables(catalogo.ascensor), ETIQUETAS_ASCENSOR),
        position=construir_opciones(
            valores_seleccionables(catalogo.localizacion), ETIQUETAS_LOCALIZACION
        ),
        floors=construir_plantas(catalogo.plantas),
        option_groups=construir_grupos(),
    )
