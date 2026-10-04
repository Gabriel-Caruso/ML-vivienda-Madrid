// Punto de entrada de la web: idioma, catálogo, registro de arranque, formulario y resultado.

import { ErrorDeRed, predecir, urlPortfolio } from "./api.js";
import {
  alCambiarEstado,
  anotar,
  esperarApi,
  estadoApi,
  iniciarRegistro,
  redibujarRegistro,
} from "./arranque.js";
import { euros, numero } from "./formato.js";
import {
  construirFormulario,
  leerPeticion,
  limpiarErrores,
  mostrarErrores,
  traducirFormulario,
} from "./formulario.js";
import {
  aplicarTraducciones,
  cargarIdioma,
  idioma,
  idiomaInicial,
  otroIdioma,
  t,
} from "./i18n.js";
import { mostrarResultado, redibujarResultado } from "./resultado.js";

let informe = null;
let ultimosErrores = null;

async function cargarJson(ruta) {
  const respuesta = await fetch(ruta);
  if (!respuesta.ok) {
    throw new Error(`No se pudo cargar ${ruta}`);
  }
  return respuesta.json();
}

function actualizarBarraEstado() {
  document.getElementById("estado-api").textContent = t(`estado.${estadoApi()}`);
  document.getElementById("estado-idioma").textContent = t("idioma.codigo");
  if (informe !== null) {
    document.getElementById("estado-modelo").textContent =
      `${informe.modelo.biblioteca} ${informe.modelo.version}`;
  }
}

function escribirMetricas() {
  const actual = idioma();
  const metricas = informe.metricas_test;
  document.getElementById("metricas-modelo").textContent = t("modelo.metricas", {
    viviendas: numero(informe.modelo.viviendas_test, actual),
    mae: euros(metricas.mae, actual),
    rmse: euros(metricas.rmse, actual),
    r2: numero(metricas.r2, actual, 3),
  });
}

function traducirPagina() {
  aplicarTraducciones();
  document.getElementById("boton-idioma").textContent = t("idioma.boton");
  traducirFormulario();
  redibujarRegistro();
  redibujarResultado();
  escribirMetricas();
  actualizarBarraEstado();
  if (ultimosErrores !== null) {
    mostrarErrores(ultimosErrores, false);
  }
}

function senalarErrores(errores) {
  ultimosErrores = errores;
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
  ultimosErrores = null;
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

  const [catalogo, informeModelo] = await Promise.all([
    cargarJson("datos/catalogo.json"),
    cargarJson("datos/informe_modelo.json"),
  ]);
  informe = informeModelo;
  construirFormulario(catalogo);
  prepararPortfolio();
  traducirPagina();

  document.getElementById("formulario").addEventListener("submit", alEnviar);
  document.getElementById("boton-idioma").addEventListener("click", alCambiarIdioma);
}

iniciar();
