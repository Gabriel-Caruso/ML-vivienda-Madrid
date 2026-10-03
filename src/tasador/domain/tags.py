"""Opciones binarias que el usuario ve en "más opciones".

Cada opción activa una o varias columnas binarias del modelo (flag_* o tag_*).
Los pares de sinónimos (reformado/reformada, estrenar/nuevo) son una sola
opción que activa ambas columnas. Las columnas binarias del modelo que no
aparecen aquí quedan fuera del contrato público y valen siempre 0.
"""

from dataclasses import dataclass

from tasador.domain.etiquetas import Etiqueta

GRUPO_VIVIENDA = "property_features"
GRUPO_LEGAL = "legal_and_listing"

ETIQUETAS_GRUPO = {
    GRUPO_VIVIENDA: Etiqueta(es="Características de la vivienda", en="Property features"),
    GRUPO_LEGAL: Etiqueta(es="Situación legal y del anuncio", en="Legal and listing status"),
}


@dataclass(frozen=True)
class OpcionBinaria:
    """Casilla del formulario y columnas del modelo que pone a 1."""

    clave: str
    columnas: tuple[str, ...]
    grupo: str
    etiqueta: Etiqueta


OPCIONES_BINARIAS = (
    # Características de la vivienda: exterior
    OpcionBinaria(
        "terrace", ("tag_terraza",), GRUPO_VIVIENDA, Etiqueta(es="Terraza", en="Terrace")
    ),
    OpcionBinaria(
        "balconies", ("tag_balcones",), GRUPO_VIVIENDA, Etiqueta(es="Balcones", en="Balconies")
    ),
    OpcionBinaria("patio", ("tag_patio",), GRUPO_VIVIENDA, Etiqueta(es="Patio", en="Patio")),
    OpcionBinaria("garden", ("tag_jardín",), GRUPO_VIVIENDA, Etiqueta(es="Jardín", en="Garden")),
    OpcionBinaria(
        "swimming_pool",
        ("tag_piscina",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Piscina", en="Swimming pool"),
    ),
    OpcionBinaria("plot", ("tag_parcela",), GRUPO_VIVIENDA, Etiqueta(es="Parcela", en="Plot")),
    OpcionBinaria("views", ("tag_vistas",), GRUPO_VIVIENDA, Etiqueta(es="Vistas", en="Views")),
    # Características de la vivienda: equipamiento
    OpcionBinaria("garage", ("tag_garaje",), GRUPO_VIVIENDA, Etiqueta(es="Garaje", en="Garage")),
    OpcionBinaria(
        "built_in_wardrobes",
        ("tag_armarios",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Armarios empotrados", en="Built-in wardrobes"),
    ),
    OpcionBinaria(
        "heating", ("tag_calefacción",), GRUPO_VIVIENDA, Etiqueta(es="Calefacción", en="Heating")
    ),
    OpcionBinaria(
        "furnished", ("tag_amueblada",), GRUPO_VIVIENDA, Etiqueta(es="Amueblada", en="Furnished")
    ),
    OpcionBinaria(
        "equipped", ("tag_equipada",), GRUPO_VIVIENDA, Etiqueta(es="Equipada", en="Equipped")
    ),
    OpcionBinaria(
        "appliances",
        ("tag_electrodomésticos",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Electrodomésticos", en="Appliances"),
    ),
    OpcionBinaria(
        "concierge", ("tag_portero",), GRUPO_VIVIENDA, Etiqueta(es="Portero", en="Concierge")
    ),
    OpcionBinaria(
        "en_suite",
        ("tag_suite",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Dormitorio en suite", en="En-suite bedroom"),
    ),
    # Características de la vivienda: estado
    OpcionBinaria(
        "renovated",
        ("tag_reformado", "tag_reformada"),
        GRUPO_VIVIENDA,
        Etiqueta(es="Reformado", en="Renovated"),
    ),
    OpcionBinaria(
        "brand_new",
        ("tag_estrenar", "tag_nuevo"),
        GRUPO_VIVIENDA,
        Etiqueta(es="A estrenar / nuevo", en="Brand new"),
    ),
    OpcionBinaria(
        "needs_renovation",
        ("tag_reformar",),
        GRUPO_VIVIENDA,
        Etiqueta(es="A reformar", en="Needs renovation"),
    ),
    # Características de la vivienda: entorno y tipo
    OpcionBinaria(
        "residential_complex",
        ("tag_urbanización",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Urbanización", en="Residential complex"),
    ),
    OpcionBinaria(
        "near_metro",
        ("tag_metro",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Cerca del metro", en="Near metro"),
    ),
    OpcionBinaria(
        "near_park",
        ("tag_parque",),
        GRUPO_VIVIENDA,
        Etiqueta(es="Cerca de un parque", en="Near a park"),
    ),
    OpcionBinaria("loft", ("flag_loft",), GRUPO_VIVIENDA, Etiqueta(es="Loft", en="Loft")),
    # Situación legal y del anuncio
    OpcionBinaria(
        "squatted",
        ("flag_okupada",),
        GRUPO_LEGAL,
        Etiqueta(es="Okupada", en="Occupied by squatters"),
    ),
    OpcionBinaria(
        "bare_ownership",
        ("flag_nuda_propiedad",),
        GRUPO_LEGAL,
        Etiqueta(es="Nuda propiedad", en="Bare ownership"),
    ),
    OpcionBinaria("auction", ("flag_subasta",), GRUPO_LEGAL, Etiqueta(es="Subasta", en="Auction")),
    OpcionBinaria(
        "tenanted",
        ("flag_alquilada",),
        GRUPO_LEGAL,
        Etiqueta(es="Alquilada (con inquilinos)", en="Tenanted"),
    ),
    OpcionBinaria(
        "joint_ownership",
        ("flag_proindiviso",),
        GRUPO_LEGAL,
        Etiqueta(es="Proindiviso", en="Undivided co-ownership"),
    ),
    OpcionBinaria(
        "price_reduced",
        ("flag_rebaja",),
        GRUPO_LEGAL,
        Etiqueta(es="Precio rebajado", en="Price reduced"),
    ),
    OpcionBinaria(
        "private_sellers_only",
        ("tag_solo_particulares",),
        GRUPO_LEGAL,
        Etiqueta(es="Solo particulares", en="Private parties only"),
    ),
    OpcionBinaria(
        "no_agencies",
        ("tag_abstenerse_agencias",),
        GRUPO_LEGAL,
        Etiqueta(es="Abstenerse agencias", en="No agencies"),
    ),
    OpcionBinaria(
        "exclusive_listing",
        ("tag_exclusiva",),
        GRUPO_LEGAL,
        Etiqueta(es="Exclusiva", en="Exclusive listing"),
    ),
)


def columnas_binarias_publicas() -> frozenset[str]:
    """Columnas binarias del modelo que el usuario puede activar."""
    columnas = set()
    for opcion in OPCIONES_BINARIAS:
        for columna in opcion.columnas:
            columnas.add(columna)
    return frozenset(columnas)
