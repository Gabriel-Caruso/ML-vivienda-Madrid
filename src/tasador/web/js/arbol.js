// Fondo: "holograma CRT" del árbol 0 real del modelo CatBoost (datos/arbol.json).
// - Proyector en la base y cono de luz hacia las hojas, como una mesa holográfica.
// - Dos copias desplazadas detrás del árbol: el modelo es un conjunto de árboles.
// - Líneas de barrido de monitor CRT por encima de todo (un patrón SVG, sin degradados).
// En reposo está quieto. Al calcular, los niveles se iluminan de arriba abajo y al
// final aparece la salida "-> PREDICCIÓN"; después se apaga nivel a nivel.
// Con prefers-reduced-motion no hay barrido: se ilumina entero y se apaga de una vez.

import { numero } from "./formato.js";
import { idioma, t } from "./i18n.js";

const SVG = "http://www.w3.org/2000/svg";
const NIVELES_NITIDOS = 5;
const NIVELES_FANTASMA = 6;
const DESPLAZAMIENTO_FANTASMA = 12;
const PASO_MS = 130;
const ESPERA_ENCENDIDO_MS = 1500;
const ESPERA_REDIMENSION_MS = 200;

let datos = null;
let svg = null;
let gruposNivel = [];
let barrido = null;
let salida = null;
let alturasNivel = [];
let temporizadores = [];

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

// Opacidad en reposo: los primeros niveles visibles y los profundos casi apagados
function opacidadNivel(nivel) {
  if (nivel < NIVELES_NITIDOS) {
    return 0.45;
  }
  return Math.max(0.08, 0.45 - (nivel - NIVELES_NITIDOS + 1) * 0.09);
}

function definirLineasCrt() {
  const definiciones = crear("defs", {}, svg);
  const patron = crear(
    "pattern",
    { id: "lineas-crt", width: 4, height: 3, patternUnits: "userSpaceOnUse" },
    definiciones,
  );
  crear("rect", { x: 0, y: 0, width: 4, height: 1, class: "holo-linea-crt" }, patron);
}

// Ramas de los primeros niveles, desplazadas: copias "detrás" del árbol principal
function dibujarFantasmas(x, y, profundidad) {
  for (const copia of [2, 1]) {
    const desplazamiento = DESPLAZAMIENTO_FANTASMA * copia;
    const grupo = crear(
      "g",
      { class: "holo-fantasma", transform: `translate(${desplazamiento} ${-desplazamiento})` },
      svg,
    );
    for (let nivel = 0; nivel < Math.min(NIVELES_FANTASMA, profundidad); nivel += 1) {
      for (let indice = 0; indice < 2 ** nivel; indice += 1) {
        for (const rama of [0, 1]) {
          crear(
            "line",
            { x1: x(nivel, indice), y1: y(nivel), x2: x(nivel + 1, 2 * indice + rama), y2: y(nivel + 1) },
            grupo,
          );
        }
      }
    }
  }
}

function dibujarProyector(ancho, alto, profundidad, x, y) {
  const centro = ancho / 2;
  const base = alto - 18;
  const proyector = crear("g", { class: "holo-proyector" }, svg);
  for (const radio of [0.1, 0.18, 0.26]) {
    crear("ellipse", { cx: centro, cy: base, rx: ancho * radio, ry: 10 + radio * 40 }, proyector);
  }
  // Cono de luz: del proyector a los extremos de la fila de hojas
  const filaHojas = y(profundidad);
  crear("line", { x1: centro, y1: base, x2: x(profundidad, 0), y2: filaHojas }, proyector);
  crear("line", { x1: centro, y1: base, x2: x(profundidad, 2 ** profundidad - 1), y2: filaHojas }, proyector);
}

function dibujar() {
  const ancho = window.innerWidth;
  const alto = window.innerHeight;
  svg.setAttribute("viewBox", `0 0 ${ancho} ${alto}`);
  svg.replaceChildren();
  detenerTemporizadores();
  definirLineasCrt();

  const profundidad = datos.profundidad;
  const arriba = alto * 0.1;
  const separacion = (alto * 0.78) / profundidad;
  function x(nivel, indice) {
    return ((indice + 0.5) * ancho) / 2 ** nivel;
  }
  function y(nivel) {
    return arriba + nivel * separacion;
  }
  alturasNivel = [];
  for (let nivel = 0; nivel <= profundidad; nivel += 1) {
    alturasNivel.push(y(nivel));
  }

  dibujarFantasmas(x, y, profundidad);
  dibujarProyector(ancho, alto, profundidad, x, y);

  const cabecera = crear("text", { x: 12, y: arriba - 28, class: "holo-texto" }, svg);
  cabecera.textContent = t("holograma.cabecera", {
    arbol: datos.arbol,
    arboles: numero(datos.arboles_en_el_modelo, idioma()),
    profundidad,
  });

  gruposNivel = [];
  for (let nivel = 0; nivel < profundidad; nivel += 1) {
    const grupo = crear("g", { class: "holo-nivel", opacity: opacidadNivel(nivel) }, svg);
    for (let indice = 0; indice < 2 ** nivel; indice += 1) {
      for (const rama of [0, 1]) {
        crear(
          "line",
          {
            x1: x(nivel, indice),
            y1: y(nivel),
            x2: x(nivel + 1, 2 * indice + rama),
            y2: y(nivel + 1),
            class: "holo-rama",
          },
          grupo,
        );
      }
    }
    const corte = crear("text", { x: 12, y: y(nivel) - 6, class: "holo-corte" }, grupo);
    corte.textContent = `${nivel}: ${datos.niveles[nivel].texto}`;
    gruposNivel.push(grupo);
  }

  barrido = crear("line", { x1: 0, x2: ancho, y1: 0, y2: 0, class: "holo-barrido" }, svg);
  barrido.setAttribute("visibility", "hidden");
  // Bajo la columna de cortes, a la izquierda: es la zona que los paneles no tapan
  salida = crear("text", { x: 12, y: y(profundidad) + 10, class: "holo-salida" }, svg);
  salida.textContent = t("holograma.salida");
  salida.setAttribute("visibility", "hidden");

  crear("rect", { x: 0, y: 0, width: ancho, height: alto, fill: "url(#lineas-crt)" }, svg);
}

function detenerTemporizadores() {
  for (const temporizador of temporizadores) {
    window.clearTimeout(temporizador);
  }
  temporizadores = [];
}

function programar(retraso, accion) {
  temporizadores.push(window.setTimeout(accion, retraso));
}

function apagarTodo() {
  for (const grupo of gruposNivel) {
    grupo.classList.remove("activo", "caliente");
  }
  barrido.setAttribute("visibility", "hidden");
  salida.setAttribute("visibility", "hidden");
}

function moverBarrido(nivel) {
  barrido.setAttribute("y1", String(alturasNivel[nivel]));
  barrido.setAttribute("y2", String(alturasNivel[nivel]));
}

// Ilumina el árbol de arriba abajo, como si el modelo procesara la vivienda.
export function activarHolograma() {
  if (svg === null) {
    return;
  }
  detenerTemporizadores();
  apagarTodo();
  const profundidad = gruposNivel.length;

  if (movimientoReducido()) {
    for (const grupo of gruposNivel) {
      grupo.classList.add("activo");
    }
    salida.setAttribute("visibility", "visible");
    programar(ESPERA_ENCENDIDO_MS, apagarTodo);
    return;
  }

  barrido.setAttribute("visibility", "visible");
  for (let nivel = 0; nivel < profundidad; nivel += 1) {
    programar(nivel * PASO_MS, function () {
      if (nivel > 0) {
        gruposNivel[nivel - 1].classList.remove("caliente");
      }
      gruposNivel[nivel].classList.add("activo", "caliente");
      moverBarrido(nivel + 1);
    });
  }
  const fin = profundidad * PASO_MS;
  programar(fin, function () {
    gruposNivel[profundidad - 1].classList.remove("caliente");
    barrido.setAttribute("visibility", "hidden");
    salida.setAttribute("visibility", "visible");
  });
  // Apagado de arriba abajo
  for (let nivel = 0; nivel < profundidad; nivel += 1) {
    programar(fin + ESPERA_ENCENDIDO_MS + nivel * PASO_MS, function () {
      gruposNivel[nivel].classList.remove("activo");
    });
  }
  programar(fin + ESPERA_ENCENDIDO_MS + profundidad * PASO_MS, function () {
    salida.setAttribute("visibility", "hidden");
  });
}

// Se vuelve a dibujar al cambiar de idioma (textos del holograma)
export function redibujarHolograma() {
  if (svg !== null) {
    dibujar();
  }
}

let esperaRedimension = null;
function alRedimensionar() {
  window.clearTimeout(esperaRedimension);
  esperaRedimension = window.setTimeout(dibujar, ESPERA_REDIMENSION_MS);
}

export function iniciarArbol(elementoSvg, datosArbol) {
  svg = elementoSvg;
  datos = datosArbol;
  dibujar();
  window.addEventListener("resize", alRedimensionar);
}
