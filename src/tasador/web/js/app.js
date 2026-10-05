// Punto de entrada de la web: idioma, catálogo, registro de arranque, formulario y resultado.

import { ErrorDeRed, predecir, urlPortfolio } from "./api.js";
import { iniciarArbol } from "./arbol.js";
import {
  alCambiarEstado,
  anotar,
  esperarApi,
  estadoApi,
  iniciarRegistro,
  redibujarRegistro,
} from "./arranque.js";
import { euros, numero, porcentaje } from "./formato.js";
import { dibujarGraficos } from "./graficos.js";
import {
  construirFormulario,
  leerPeticion,
  limpiarErrores,
  mostrarErrores,
  redibujarErrores,
  traducirFormulario,
} from "./formulario.js";
import {
  aplicarTraducciones,
  cargarIdioma,
  escribirConResaltado,
  idioma,
  idiomaInicial,
  otroIdioma,
  t,
} from "./i18n.js";
import { mostrarResultado, redibujarResultado, ultimoResultado } from "./resultado.js";

const ESPERA_REDIMENSION_MS = 150;

let informe = null;
let catalogo = null;

function redibujarGraficos() {
  if (informe !== null) {
    dibujarGraficos(informe, ultimoResultado());
  }
}

let esperaRedimension = null;
function alRedimensionar() {
  window.clearTimeout(esperaRedimension);
  esperaRedimension = window.setTimeout(redibujarGraficos, ESPERA_REDIMENSION_MS);
}

async function cargarJson(ruta) {
  const respuesta = await fetch(ruta);
  if (!respuesta.ok) {
    throw new Error(`No se pudo cargar ${ruta}`);
  }
  return respuesta.json();
}

function actualizarBarraEstado() {
  const estadoApiElemento = document.getElementById("estado-api");
  estadoApiElemento.textContent = t(`estado.${estadoApi()}`);
  estadoApiElemento.dataset.estado = estadoApi();
  document.getElementById("estado-idioma").textContent = t("idioma.codigo");
  if (informe !== null) {
    document.getElementById("estado-modelo").textContent =
      `${informe.modelo.biblioteca} ${informe.modelo.version}`;
  }
}

// Textos de "sobre el modelo" con sus cifras reales (informe y catálogo).
function escribirTextosModelo() {
  const actual = idioma();
  const tramos = informe.error_por_tramo;
  let errorMinimo = tramos[0].error_relativo;
  let errorMaximo = tramos[0].error_relativo;
  for (let posicion = 0; posicion < tramos.length - 1; posicion += 1) {
    errorMinimo = Math.min(errorMinimo, tramos[posicion].error_relativo);
    errorMaximo = Math.max(errorMaximo, tramos[posicion].error_relativo);
  }
  const lujo = tramos[tramos.length - 1];
  let barrios = 0;
  for (const distrito of catalogo.districts) {
    barrios += distrito.neighbourhoods.length;
  }
  const metricas = informe.metricas_test;
  const parametros = {
    que_es: {
      arboles: numero(informe.modelo.arboles, actual),
      profundidad: informe.modelo.profundidad,
      variables: informe.modelo.variables,
      indicadores: informe.modelo.variables - catalogo.fields.length,
    },
    precision: {
      viviendas: numero(informe.modelo.viviendas_test, actual),
      mae: euros(metricas.mae, actual),
      rmse: euros(metricas.rmse, actual),
      r2: numero(metricas.r2, actual, 3),
      error_min: porcentaje(errorMinimo, actual, 1),
      error_max: porcentaje(errorMaximo, actual, 1),
      error_lujo: porcentaje(lujo.error_relativo, actual, 1),
      umbral: numero(lujo.limite_inferior / 1000000, actual, 2),
    },
    limitaciones: { distritos: catalogo.districts.length, barrios },
    autoria: {},
  };
  for (const parrafo of document.querySelectorAll("[data-texto-modelo]")) {
    const clave = parrafo.dataset.textoModelo;
    escribirConResaltado(parrafo, t(`modelo.${clave}`, parametros[clave]));
  }
}

function traducirPagina() {
  aplicarTraducciones();
  document.getElementById("boton-idioma").textContent = t("idioma.boton");
  traducirFormulario();
  redibujarRegistro();
  redibujarResultado();
  escribirTextosModelo();
  redibujarGraficos();
  actualizarBarraEstado();
  redibujarErrores();
}

function senalarErrores(errores) {
  mostrarErrores(errores);
}

function bloquearBoton(bloqueado) {
  const boton = document.getElementById("boton-calcular");
  boton.disabled = bloqueado;
  boton.textContent = t(bloqueado ? "formulario.calculando" : "formulario.calcular");
}

async function alEnviar(evento) {
  evento.preventDefault();
  limpiarErrores();
  const { peticion, errores } = leerPeticion();
  if (errores.length > 0) {
    senalarErrores(errores);
    return;
  }

  bloquearBoton(true);
  try {
    if (estadoApi() !== "online") {
      anotar("arranque.en_cola");
    }
    const preparada = await esperarApi();
    if (!preparada) {
      senalarErrores([{ code: "RED", field: null, params: {} }]);
      return;
    }
    anotar("arranque.calculando");
    const respuesta = await predecir(peticion);
    if (respuesta.ok) {
      anotar("arranque.recibido");
      mostrarResultado(respuesta.cuerpo);
      redibujarGraficos();
    } else if (respuesta.cuerpo && Array.isArray(respuesta.cuerpo.errors)) {
      anotar("arranque.rechazado");
      senalarErrores(respuesta.cuerpo.errors);
    } else {
      senalarErrores([{ code: "DESCONOCIDO", field: null, params: {} }]);
    }
  } catch (error) {
    if (!(error instanceof ErrorDeRed)) {
      throw error;
    }
    senalarErrores([{ code: "RED", field: null, params: {} }]);
  } finally {
    bloquearBoton(false);
  }
}

async function alCambiarIdioma() {
  await cargarIdioma(otroIdioma());
  traducirPagina();
}

function prepararPortfolio() {
  const direccion = urlPortfolio();
  if (direccion !== "") {
    const elementoLista = document.getElementById("enlace-portfolio");
    elementoLista.querySelector("a").href = direccion;
    elementoLista.hidden = false;
  }
}

async function iniciar() {
  iniciarRegistro(document.getElementById("registro"));
  await cargarIdioma(idiomaInicial());
  aplicarTraducciones();
  alCambiarEstado(actualizarBarraEstado);

  // La API empieza a despertar ya; el formulario no la espera
  esperarApi();

  const [catalogoWeb, informeModelo, arbol] = await Promise.all([
    cargarJson("datos/catalogo.json"),
    cargarJson("datos/informe_modelo.json"),
    cargarJson("datos/arbol.json"),
  ]);
  informe = informeModelo;
  catalogo = catalogoWeb;
  iniciarArbol(document.getElementById("fondo-arbol"), arbol);
  construirFormulario(catalogo);
  prepararPortfolio();
  traducirPagina();

  document.getElementById("formulario").addEventListener("submit", alEnviar);
  document.getElementById("boton-idioma").addEventListener("click", alCambiarIdioma);
  window.addEventListener("resize", alRedimensionar);
}

iniciar();
