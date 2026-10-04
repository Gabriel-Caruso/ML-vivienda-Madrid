// Resultado de la tasación. Se anuncia con aria-live desde el contenedor #resultado.

import { euros, porcentaje, redondearAMiles } from "./formato.js";
import { idioma, t } from "./i18n.js";

let ultimo = null;

function parrafo(clase, texto) {
  const elemento = document.createElement("p");
  elemento.className = clase;
  elemento.textContent = texto;
  return elemento;
}

function dibujar() {
  const actual = idioma();
  const contenedor = document.getElementById("resultado");
  contenedor.replaceChildren(
    parrafo("resultado-etiqueta", t("resultado.precio")),
    parrafo("resultado-precio", euros(redondearAMiles(ultimo.estimated_price), actual)),
    parrafo(
      "resultado-margen",
      t("resultado.margen", { margen: porcentaje(ultimo.error_margin, actual) }),
    ),
    parrafo(
      "resultado-horquilla",
      t("resultado.horquilla", {
        minimo: euros(ultimo.price_min, actual),
        maximo: euros(ultimo.price_max, actual),
      }),
    ),
  );
}

// datos: respuesta de POST /api/v1/predict.
export function mostrarResultado(datos) {
  ultimo = datos;
  dibujar();
}

export function redibujarResultado() {
  if (ultimo !== null) {
    dibujar();
  }
}

export function ultimoResultado() {
  return ultimo;
}
