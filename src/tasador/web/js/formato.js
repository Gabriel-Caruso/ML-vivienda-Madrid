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

// Euros abreviados para ejes: 435k, 1,49M (es) / 1.49M (en).
export function eurosCortos(valor, idioma) {
  if (valor >= 1000000) {
    return `${numeroCorto(valor / 1000000, idioma, 2)}M`;
  }
  return `${numeroCorto(valor / 1000, idioma, 0)}k`;
}

function numeroCorto(valor, idioma, decimales) {
  return new Intl.NumberFormat(LOCALES[idioma], { maximumFractionDigits: decimales }).format(valor);
}
