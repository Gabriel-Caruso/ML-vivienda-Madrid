// Registro de arranque y estado de la API.
// Las líneas se guardan como claves de traducción para poder redibujarlas al
// cambiar de idioma.

import { comprobarSalud, ErrorDeRed } from "./api.js";
import { t } from "./i18n.js";

const AVISO_REPOSO_MS = 2500;
const INTERVALO_LATIDO_MS = 15000;
const INTERVALO_REINTENTO_MS = 3000;
const LIMITE_ESPERA_MS = 150000;

const lineas = [];
const oyentesEstado = [];
let lista = null;
let estado = "conectando";
let promesaEnCurso = null;

export function iniciarRegistro(elementoLista) {
  lista = elementoLista;
}

export function anotar(clave, parametros = {}) {
  lineas.push({ clave, parametros });
  const elemento = document.createElement("li");
  elemento.textContent = t(clave, parametros);
  lista.append(elemento);
}

export function redibujarRegistro() {
  lista.replaceChildren();
  for (const linea of lineas) {
    const elemento = document.createElement("li");
    elemento.textContent = t(linea.clave, linea.parametros);
    lista.append(elemento);
  }
}

export function estadoApi() {
  return estado;
}

export function alCambiarEstado(oyente) {
  oyentesEstado.push(oyente);
}

function cambiarEstado(nuevo) {
  estado = nuevo;
  for (const oyente of oyentesEstado) {
    oyente(nuevo);
  }
}

function pausa(milisegundos) {
  return new Promise(function (resolver) {
    window.setTimeout(resolver, milisegundos);
  });
}

async function despertar() {
  anotar("arranque.conectando");
  cambiarEstado("conectando");
  const inicio = Date.now();

  function avisarReposo() {
    anotar("arranque.reposo");
    cambiarEstado("despertando");
  }
  function latido() {
    anotar("arranque.sigue", { segundos: Math.round((Date.now() - inicio) / 1000) });
  }
  const temporizadorReposo = window.setTimeout(avisarReposo, AVISO_REPOSO_MS);
  const temporizadorLatido = window.setInterval(latido, INTERVALO_LATIDO_MS);

  try {
    while (Date.now() - inicio < LIMITE_ESPERA_MS) {
      let preparada = false;
      try {
        preparada = await comprobarSalud();
      } catch (error) {
        if (!(error instanceof ErrorDeRed)) {
          throw error;
        }
      }
      if (preparada) {
        anotar("arranque.listo");
        cambiarEstado("online");
        return true;
      }
      if (estado === "conectando") {
        window.clearTimeout(temporizadorReposo);
        avisarReposo();
      }
      await pausa(INTERVALO_REINTENTO_MS);
    }
    anotar("arranque.sin_conexion");
    cambiarEstado("offline");
    return false;
  } finally {
    window.clearTimeout(temporizadorReposo);
    window.clearInterval(temporizadorLatido);
  }
}

// Espera a que la API esté lista. Si ya hay una espera en curso, se reutiliza;
// si la última terminó sin conexión, se vuelve a intentar.
export async function esperarApi() {
  if (estado === "online") {
    return true;
  }
  if (promesaEnCurso === null) {
    promesaEnCurso = despertar();
  }
  const preparada = await promesaEnCurso;
  promesaEnCurso = null;
  return preparada;
}
