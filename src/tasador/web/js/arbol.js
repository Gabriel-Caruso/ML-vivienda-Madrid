// Fondo: el árbol 0 real del modelo (datos/arbol.json).
// Árbol simétrico de 9 niveles: los 5 primeros nítidos y el resto desvaneciéndose.
// En bucle lento, una vivienda real de los fixtures baja por el árbol nivel a nivel.
// Con prefers-reduced-motion el recorrido se muestra fijo, sin animación.

const SVG = "http://www.w3.org/2000/svg";
const NIVELES_NITIDOS = 5;
const PASO_MS = 1600;
const PAUSA_FINAL_MS = 4000;
const ESPERA_REDIMENSION_MS = 200;

let datos = null;
let svg = null;
let ramas = new Map();
let temporizador = null;
let recorridoActual = 0;
let nivelActual = 0;

function crear(nombre, atributos, padre) {
  const elemento = document.createElementNS(SVG, nombre);
  for (const [clave, valor] of Object.entries(atributos)) {
    elemento.setAttribute(clave, String(valor));
  }
  padre.append(elemento);
  return elemento;
}

function movimientoReducido() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

// Opacidad de un nivel: 1 en los nítidos y menor cuanto más profundo.
function opacidadNivel(nivel) {
  if (nivel < NIVELES_NITIDOS) {
    return 1;
  }
  return Math.max(0.12, 1 - (nivel - NIVELES_NITIDOS + 1) * 0.22);
}

function dibujar() {
  const ancho = window.innerWidth;
  const alto = window.innerHeight;
  svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
  svg.replaceChildren();
  ramas = new Map();

  const profundidad = datos.profundidad;
  const arriba = alto * 0.08;
  const separacion = (alto * 0.86) / profundidad;
  function x(nivel, indice) {
    return ((indice + 0.5) * ancho) / 2 ** nivel;
  }
  function y(nivel) {
    return arriba + nivel * separacion;
  }

  for (let nivel = 0; nivel < profundidad; nivel += 1) {
    const grupo = crear("g", { opacity: opacidadNivel(nivel) }, svg);
    for (let indice = 0; indice < 2 ** nivel; indice += 1) {
      for (const rama of [0, 1]) {
        const hijo = 2 * indice + rama;
        const linea = crear(
          "line",
          { x1: x(nivel, indice), y1: y(nivel), x2: x(nivel + 1, hijo), y2: y(nivel + 1), class: "rama" },
          grupo,
        );
        ramas.set(`${nivel}-${indice}-${rama}`, linea);
      }
    }
    const corte = crear("text", { x: 12, y: y(nivel) - 6, class: "corte" }, grupo);
    corte.textContent = `${nivel}: ${datos.niveles[nivel].texto}`;
  }
}

function limpiarRecorrido() {
  for (const linea of svg.querySelectorAll(".rama-recorrida")) {
    linea.classList.remove("rama-recorrida");
  }
}

// Marca las ramas del recorrido hasta el nivel indicado (sin incluirlo).
function marcarRecorrido(indiceRecorrido, hastaNivel) {
  const elegidas = datos.recorridos[indiceRecorrido].ramas;
  let nodo = 0;
  for (let nivel = 0; nivel < hastaNivel; nivel += 1) {
    const rama = elegidas[nivel];
    ramas.get(`${nivel}-${nodo}-${rama}`).classList.add("rama-recorrida");
    nodo = 2 * nodo + rama;
  }
}

function paso() {
  if (nivelActual === 0) {
    limpiarRecorrido();
  }
  nivelActual += 1;
  marcarRecorrido(recorridoActual, nivelActual);
  if (nivelActual >= datos.profundidad) {
    nivelActual = 0;
    recorridoActual = (recorridoActual + 1) % datos.recorridos.length;
    temporizador = window.setTimeout(paso, PAUSA_FINAL_MS);
  } else {
    temporizador = window.setTimeout(paso, PASO_MS);
  }
}

function detener() {
  if (temporizador !== null) {
    window.clearTimeout(temporizador);
    temporizador = null;
  }
}

function arrancar() {
  detener();
  limpiarRecorrido();
  if (movimientoReducido()) {
    marcarRecorrido(0, datos.profundidad);
    return;
  }
  nivelActual = 0;
  temporizador = window.setTimeout(paso, PASO_MS);
}

function alCambiarVisibilidad() {
  if (document.hidden) {
    detener();
  } else {
    arrancar();
  }
}

let esperaRedimension = null;
function alRedimensionar() {
  window.clearTimeout(esperaRedimension);
  esperaRedimension = window.setTimeout(function () {
    dibujar();
    arrancar();
  }, ESPERA_REDIMENSION_MS);
}

export function iniciarArbol(elementoSvg, datosArbol) {
  svg = elementoSvg;
  datos = datosArbol;
  dibujar();
  arrancar();
  window.addEventListener("resize", alRedimensionar);
  document.addEventListener("visibilitychange", alCambiarVisibilidad);
  window.matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", arrancar);
}
