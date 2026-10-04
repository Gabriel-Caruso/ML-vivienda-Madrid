// Traducciones: diccionarios i18n/es.json e i18n/en.json.
// Los elementos con data-i18n="clave.anidada" reciben el texto de esa clave.

const IDIOMAS = ["es", "en"];
const CLAVE_ALMACEN = "tasador.idioma";

let idiomaActual = "es";
let diccionario = {};

export function idioma() {
  return idiomaActual;
}

export function otroIdioma() {
  return idiomaActual === "es" ? "en" : "es";
}

// Idioma guardado si existe; si no, el del navegador (español o, si no, inglés).
export function idiomaInicial() {
  try {
    const guardado = window.localStorage.getItem(CLAVE_ALMACEN);
    if (IDIOMAS.includes(guardado)) {
      return guardado;
    }
  } catch (error) {
    // Almacenamiento no disponible (modo privado o bloqueado): se usa el navegador
  }
  const preferidos = navigator.languages || [navigator.language || "es"];
  for (const preferido of preferidos) {
    if (preferido.toLowerCase().startsWith("es")) {
      return "es";
    }
    if (preferido.toLowerCase().startsWith("en")) {
      return "en";
    }
  }
  return "en";
}

export async function cargarIdioma(nuevoIdioma) {
  const respuesta = await fetch(`i18n/${nuevoIdioma}.json`);
  if (!respuesta.ok) {
    throw new Error(`No se pudo cargar el idioma ${nuevoIdioma}`);
  }
  diccionario = await respuesta.json();
  idiomaActual = nuevoIdioma;
  document.documentElement.lang = nuevoIdioma;
  try {
    window.localStorage.setItem(CLAVE_ALMACEN, nuevoIdioma);
  } catch (error) {
    // Sin almacenamiento la elección dura lo que la visita
  }
}

// Texto de una clave con sus {parametros} sustituidos. Si falta, devuelve la clave.
export function t(clave, parametros = {}) {
  let valor = diccionario;
  for (const parte of clave.split(".")) {
    if (valor === undefined || valor === null) {
      break;
    }
    valor = valor[parte];
  }
  if (typeof valor !== "string") {
    return clave;
  }
  let texto = valor;
  for (const [nombre, sustituto] of Object.entries(parametros)) {
    texto = texto.replaceAll(`{${nombre}}`, String(sustituto));
  }
  return texto;
}

export function aplicarTraducciones(raiz = document) {
  for (const elemento of raiz.querySelectorAll("[data-i18n]")) {
    elemento.textContent = t(elemento.dataset.i18n);
  }
}

// Texto de una etiqueta bilingüe del catálogo ({es, en}) en el idioma actual.
export function etiqueta(bilingue) {
  return bilingue[idiomaActual];
}
