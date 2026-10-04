// Formato de números y precios según el idioma: 450.000 € en español, €450,000 en inglés.

const LOCALES = { es: "es-ES", en: "en-GB" };

export function locale(idioma) {
  return LOCALES[idioma];
}

export function euros(valor, idioma) {
  return new Intl.NumberFormat(LOCALES[idioma], {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
    useGrouping: "always",
  }).format(valor);
}

export function redondearAMiles(valor) {
  return Math.round(valor / 1000) * 1000;
}

export function porcentaje(fraccion, idioma, decimales = 0) {
  return new Intl.NumberFormat(LOCALES[idioma], {
    style: "percent",
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
  }).format(fraccion);
}

export function numero(valor, idioma, decimales = 0) {
  return new Intl.NumberFormat(LOCALES[idioma], {
    minimumFractionDigits: decimales,
    maximumFractionDigits: decimales,
    useGrouping: "always",
  }).format(valor);
}
