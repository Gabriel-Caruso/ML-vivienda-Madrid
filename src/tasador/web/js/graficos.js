// Gráficos A-D en SVG propio, a partir de datos/informe_modelo.json.
// Se dibujan al ancho real de su contenedor para que el texto mantenga su tamaño.
// Cada marca lleva un <title> (información al pasar el ratón) y cada gráfico un
// aria-label con su resumen. Las series se distinguen por forma o trazo, no por color.

import { euros, eurosCortos, numero, porcentaje, redondearAMiles } from "./formato.js";
import { etiqueta, idioma, t } from "./i18n.js";

const SVG = "http://www.w3.org/2000/svg";
const ANCHO_POR_DEFECTO = 560;
const LIMITE_DIBUJADAS_C = 10;
// Por debajo de este ancho (px) los gráficos usan una disposición compacta
const ANCHO_ESTRECHO = 480;
// Ancho aproximado de un carácter de IBM Plex Mono a 12 px
const ANCHO_CARACTER = 7.3;

// --- Utilidades SVG --------------------------------------------------------

function crear(nombre, atributos, padre) {
  const elemento = document.createElementNS(SVG, nombre);
  for (const [clave, valor] of Object.entries(atributos)) {
    elemento.setAttribute(clave, String(valor));
  }
  if (padre) {
    padre.append(elemento);
  }
  return elemento;
}

function escribir(padre, x, y, contenido, clase, ancla = "start") {
  const elemento = crear("text", { x, y, class: clase, "text-anchor": ancla }, padre);
  elemento.textContent = contenido;
  return elemento;
}

function titular(elemento, contenido) {
  crear("title", {}, elemento).textContent = contenido;
}

function anchoDisponible(idContenedor) {
  const contenedor = document.getElementById(idContenedor);
  return Math.max(280, Math.floor(contenedor.clientWidth || ANCHO_POR_DEFECTO));
}

function anchoTexto(contenido) {
  return contenido.length * ANCHO_CARACTER;
}

function nuevoLienzo(idContenedor, alto, resumen) {
  const contenedor = document.getElementById(idContenedor);
  const ancho = anchoDisponible(idContenedor);
  const svg = crear("svg", {
    viewBox: `0 0 ${ancho} ${alto}`,
    width: ancho,
    height: alto,
    role: "img",
    "aria-label": resumen,
  });
  contenedor.replaceChildren(svg);
  return { svg, ancho, alto };
}

// Índice del tramo en que cae un precio: el último cuyo límite inferior no lo supera.
function indiceTramo(tramos, precio) {
  let indice = 0;
  for (let posicion = 0; posicion < tramos.length; posicion += 1) {
    if (precio >= tramos[posicion].limite_inferior) {
      indice = posicion;
    }
  }
  return indice;
}

// --- Gráfico A: error relativo por tramo de precio ------------------------

function dibujarGraficoA(informe, resultado) {
  const actual = idioma();
  const tramos = informe.error_por_tramo;
  const margen = { izquierda: 48, derecha: 8, arriba: 24, abajo: 72 };
  const { svg, ancho, alto } = nuevoLienzo("lienzo-grafico-a", 256, t("graficos.a.titulo"));
  const anchoUtil = ancho - margen.izquierda - margen.derecha;
  const altoUtil = alto - margen.arriba - margen.abajo;

  let maximo = 0;
  for (const tramo of tramos) {
    maximo = Math.max(maximo, tramo.error_relativo);
  }
  const techo = Math.ceil(maximo * 20) / 20 + 0.05;
  function y(valor) {
    return margen.arriba + altoUtil * (1 - valor / techo);
  }

  for (let marca = 0; marca <= techo + 1e-9; marca += 0.05) {
    crear("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(marca), y2: y(marca), class: "rejilla" }, svg);
    escribir(svg, margen.izquierda - 6, y(marca) + 4, porcentaje(marca, actual), "texto-eje", "end");
  }
  crear("line", { x1: margen.izquierda, x2: margen.izquierda, y1: margen.arriba, y2: alto - margen.abajo, class: "eje" }, svg);
  crear("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: alto - margen.abajo, y2: alto - margen.abajo, class: "eje" }, svg);
  escribir(svg, margen.izquierda, 12, t("graficos.a.eje_y"), "titulo-eje");

  const marcado = resultado ? indiceTramo(tramos, resultado.estimated_price) : -1;
  const anchoTramo = anchoUtil / tramos.length;
  for (let posicion = 0; posicion < tramos.length; posicion += 1) {
    const tramo = tramos[posicion];
    const centro = margen.izquierda + anchoTramo * (posicion + 0.5);
    const anchoBarra = anchoTramo * 0.6;
    const nombreTramo = `${eurosCortos(tramo.limite_inferior, actual)}-${eurosCortos(tramo.limite_superior, actual)}`;
    const esMarcado = posicion === marcado;

    const barra = crear(
      "rect",
      {
        x: centro - anchoBarra / 2,
        y: y(tramo.error_relativo),
        width: anchoBarra,
        height: y(0) - y(tramo.error_relativo),
        class: esMarcado ? "barra barra-marcada" : "barra",
      },
      svg,
    );
    titular(
      barra,
      t("graficos.a.barra", {
        tramo: nombreTramo,
        error: porcentaje(tramo.error_relativo, actual, 1),
        mae: euros(tramo.mae, actual),
        mediana: euros(tramo.precio_mediano, actual),
        viviendas: numero(tramo.viviendas, actual),
      }),
    );
    escribir(
      svg,
      centro,
      y(tramo.error_relativo) - 6,
      porcentaje(tramo.error_relativo, actual, 1),
      esMarcado ? "texto-marcado" : "texto-valor",
      "middle",
    );
    // Si la etiqueta no cabe en el ancho del tramo, se parte en dos líneas: "35k-" / "250k"
    if (anchoTexto(nombreTramo) > anchoTramo - 4) {
      escribir(svg, centro, alto - margen.abajo + 18, `${eurosCortos(tramo.limite_inferior, actual)}-`, "texto-eje", "middle");
      escribir(svg, centro, alto - margen.abajo + 32, eurosCortos(tramo.limite_superior, actual), "texto-eje", "middle");
    } else {
      escribir(svg, centro, alto - margen.abajo + 18, nombreTramo, "texto-eje", "middle");
    }
    if (esMarcado) {
      // La etiqueta completa, desplazada lo justo para no salirse del gráfico
      const textoMarcado = `[${t("graficos.a.tu_tramo")}]`;
      const mitad = anchoTexto(textoMarcado) / 2;
      const xEtiqueta = Math.min(Math.max(centro, mitad), ancho - mitad);
      escribir(svg, xEtiqueta, alto - margen.abajo + 52, textoMarcado, "texto-marcado", "middle");
    }
  }
}

// --- Gráfico B: precio real frente a predicho, escala logarítmica ---------

const MARCAS_LOG = [50000, 100000, 200000, 500000, 1000000, 2000000, 5000000, 10000000];
const MARCAS_LOG_ESTRECHO = [100000, 1000000, 10000000];

function dibujarGraficoB(informe, resultado) {
  const actual = idioma();
  const puntos = informe.real_frente_a_predicho;
  const resumen = t("graficos.b.resumen", { viviendas: numero(puntos.reales.length, actual) });
  const anchoContenedor = document.getElementById("lienzo-grafico-b").clientWidth || ANCHO_POR_DEFECTO;
  const alto = Math.round(Math.min(420, Math.max(300, anchoContenedor * 0.8)));
  const { svg, ancho } = nuevoLienzo("lienzo-grafico-b", alto, resumen);
  const margen = { izquierda: 52, derecha: 12, arriba: 76, abajo: 44 };

  const minimo = Math.log10(30000);
  const maximo = Math.log10(15000000);
  function x(valor) {
    return margen.izquierda + ((Math.log10(valor) - minimo) / (maximo - minimo)) * (ancho - margen.izquierda - margen.derecha);
  }
  function y(valor) {
    return alto - margen.abajo - ((Math.log10(valor) - minimo) / (maximo - minimo)) * (alto - margen.arriba - margen.abajo);
  }

  for (const marca of MARCAS_LOG) {
    crear("line", { x1: x(marca), x2: x(marca), y1: margen.arriba, y2: alto - margen.abajo, class: "rejilla" }, svg);
    crear("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(marca), y2: y(marca), class: "rejilla" }, svg);
    if (ancho >= ANCHO_ESTRECHO || MARCAS_LOG_ESTRECHO.includes(marca)) {
      escribir(svg, x(marca), alto - margen.abajo + 16, eurosCortos(marca, actual), "texto-eje", "middle");
    }
    escribir(svg, margen.izquierda - 6, y(marca) + 4, eurosCortos(marca, actual), "texto-eje", "end");
  }
  crear("line", { x1: margen.izquierda, x2: margen.izquierda, y1: margen.arriba, y2: alto - margen.abajo, class: "eje" }, svg);
  crear("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: alto - margen.abajo, y2: alto - margen.abajo, class: "eje" }, svg);
  escribir(svg, ancho - margen.derecha, alto - 6, t("graficos.b.eje_x"), "titulo-eje", "end");
  escribir(svg, margen.izquierda, margen.arriba - 8, t("graficos.b.eje_y"), "titulo-eje");

  const grupo = crear("g", {}, svg);
  titular(grupo, resumen);
  for (let posicion = 0; posicion < puntos.reales.length; posicion += 1) {
    crear("rect", { x: x(puntos.reales[posicion]) - 1, y: y(puntos.predichos[posicion]) - 1, width: 2, height: 2, class: "punto" }, grupo);
  }

  const diagonal = crear("line", { x1: x(30000), y1: y(30000), x2: x(15000000), y2: y(15000000), class: "diagonal" }, svg);
  titular(diagonal, t("graficos.b.diagonal"));

  // Leyenda: forma o trazo de cada serie, con su nombre
  let cursor = margen.izquierda;
  const filaLeyenda = 14;
  crear("rect", { x: cursor, y: filaLeyenda - 5, width: 4, height: 4, class: "marcador" }, svg);
  cursor += 10;
  cursor = escribirLeyenda(svg, cursor, filaLeyenda, t("graficos.b.puntos"));
  crear("line", { x1: cursor, x2: cursor + 22, y1: filaLeyenda - 3, y2: filaLeyenda - 3, class: "diagonal" }, svg);
  cursor = escribirLeyenda(svg, cursor + 28, filaLeyenda, t("graficos.b.diagonal"));

  if (resultado) {
    const precio = resultado.estimated_price;
    const linea = crear("line", { x1: margen.izquierda, x2: ancho - margen.derecha, y1: y(precio), y2: y(precio), class: "linea-usuario" }, svg);
    const etiquetaUsuario = `${t("graficos.b.tu_estimacion")}: ${euros(redondearAMiles(precio), actual)}`;
    titular(linea, etiquetaUsuario);
    // Fondo opaco tras la etiqueta para que se lea sobre la nube de puntos
    const anchoEtiqueta = etiquetaUsuario.length * 7.6 + 8;
    crear("rect", { x: ancho - margen.derecha - anchoEtiqueta, y: y(precio) - 20, width: anchoEtiqueta, height: 16, class: "fondo-etiqueta" }, svg);
    escribir(svg, ancho - margen.derecha - 4, y(precio) - 8, etiquetaUsuario, "texto-marcado", "end");
    crear("line", { x1: margen.izquierda, x2: margen.izquierda + 22, y1: filaLeyenda + 15, y2: filaLeyenda + 15, class: "linea-usuario" }, svg);
    escribirLeyenda(svg, margen.izquierda + 28, filaLeyenda + 18, t("graficos.b.tu_estimacion"));
  }
}

// Escribe un texto de leyenda y devuelve la x donde puede empezar el siguiente elemento.
function escribirLeyenda(svg, x, y, contenido) {
  escribir(svg, x, y, contenido, "texto-eje");
  return x + contenido.length * 7.4 + 16;
}

// --- Gráfico C: importancia de variables -----------------------------------

function dibujarGraficoC(informe) {
  const actual = idioma();
  const variables = informe.importancia_variables;
  const filas = [];
  let resto = 0;
  for (let posicion = 0; posicion < variables.length; posicion += 1) {
    if (posicion < LIMITE_DIBUJADAS_C) {
      filas.push({ texto: etiqueta(variables[posicion].etiqueta), valor: variables[posicion].importancia, agrupada: false });
    } else {
      resto += variables[posicion].importancia;
    }
  }
  filas.push({ texto: t("graficos.c.otras"), valor: resto, agrupada: true });

  const altoFila = 22;
  const margen = { izquierda: 0, derecha: 56, arriba: 8, abajo: 32 };
  const alto = margen.arriba + filas.length * altoFila + margen.abajo;
  const { svg, ancho } = nuevoLienzo("lienzo-grafico-c", alto, t("graficos.c.titulo"));
  margen.izquierda = Math.min(200, Math.round(ancho * 0.42));

  let maximo = 0;
  for (const fila of filas) {
    maximo = Math.max(maximo, fila.valor);
  }
  const techo = Math.ceil(maximo / 10) * 10;
  function x(valor) {
    return margen.izquierda + (valor / techo) * (ancho - margen.izquierda - margen.derecha);
  }

  for (let marca = 0; marca <= techo; marca += 10) {
    crear("line", { x1: x(marca), x2: x(marca), y1: margen.arriba, y2: alto - margen.abajo, class: "rejilla" }, svg);
    escribir(svg, x(marca), alto - margen.abajo + 16, String(marca), "texto-eje", "middle");
  }
  crear("line", { x1: margen.izquierda, x2: margen.izquierda, y1: margen.arriba, y2: alto - margen.abajo, class: "eje" }, svg);
  escribir(svg, ancho - margen.derecha, alto - 4, t("graficos.c.eje_x"), "titulo-eje", "end");

  for (let posicion = 0; posicion < filas.length; posicion += 1) {
    const fila = filas[posicion];
    const arriba = margen.arriba + posicion * altoFila;
    const valorTexto = porcentaje(fila.valor / 100, actual, 1);
    escribir(svg, margen.izquierda - 8, arriba + 15, fila.texto, "texto-eje", "end");
    const barra = crear(
      "rect",
      {
        x: margen.izquierda,
        y: arriba + 4,
        width: Math.max(1, x(fila.valor) - margen.izquierda),
        height: altoFila - 8,
        class: fila.agrupada ? "barra" : "barra barra-llena",
      },
      svg,
    );
    if (fila.agrupada) {
      barra.setAttribute("stroke-dasharray", "4 3");
    }
    titular(barra, t("graficos.c.barra", { variable: fila.texto, valor: valorTexto }));
    escribir(svg, x(fila.valor) + 6, arriba + 15, valorTexto, "texto-valor");
  }
}

// --- Gráfico D: MAE por modelo -------------------------------------------

function dibujarMarcador(svg, x, y, conjunto) {
  if (conjunto === "test") {
    return crear("path", { d: `M${x} ${y - 6}L${x + 6} ${y}L${x} ${y + 6}L${x - 6} ${y}Z`, class: "marcador-hueco" }, svg);
  }
  return crear("rect", { x: x - 4, y: y - 4, width: 8, height: 8, class: "marcador" }, svg);
}

function dibujarGraficoD(informe) {
  const actual = idioma();
  const serie = informe.mae_por_modelo;
  // En pantallas estrechas el nombre de cada modelo va encima de su punto
  const estrecho = anchoDisponible("lienzo-grafico-d") < ANCHO_ESTRECHO;
  const altoFila = estrecho ? 40 : 26;
  const textoCv = t("graficos.d.cv");
  const textoTest = t("graficos.d.test");
  const leyendaEnDosFilas = estrecho;
  const margen = { izquierda: 0, derecha: 88, arriba: leyendaEnDosFilas ? 52 : 36, abajo: 32 };
  const alto = margen.arriba + serie.length * altoFila + margen.abajo;
  const { svg, ancho } = nuevoLienzo("lienzo-grafico-d", alto, t("graficos.d.titulo"));
  margen.izquierda = estrecho ? 8 : Math.min(200, Math.round(ancho * 0.42));

  let maximo = 0;
  for (const punto of serie) {
    maximo = Math.max(maximo, punto.mae);
  }
  const techo = Math.ceil(maximo / 100000) * 100000;
  function x(valor) {
    return margen.izquierda + (valor / techo) * (ancho - margen.izquierda - margen.derecha);
  }
  function centroFila(posicion) {
    const arriba = margen.arriba + posicion * altoFila;
    return estrecho ? arriba + 28 : arriba + altoFila / 2;
  }

  for (let marca = 0; marca <= techo; marca += 100000) {
    crear("line", { x1: x(marca), x2: x(marca), y1: margen.arriba, y2: alto - margen.abajo, class: "rejilla" }, svg);
    escribir(svg, x(marca), alto - margen.abajo + 16, eurosCortos(marca, actual), "texto-eje", "middle");
  }
  escribir(svg, ancho - margen.derecha, alto - 4, t("graficos.d.eje_x"), "titulo-eje", "end");

  // Leyenda: cuadrado relleno para validación cruzada, rombo hueco para test
  dibujarMarcador(svg, 6, 12, "cv");
  const siguiente = escribirLeyenda(svg, 16, 16, textoCv);
  if (leyendaEnDosFilas) {
    dibujarMarcador(svg, 6, 32, "test");
    escribirLeyenda(svg, 16, 36, textoTest);
  } else {
    dibujarMarcador(svg, siguiente + 6, 12, "test");
    escribirLeyenda(svg, siguiente + 16, 16, textoTest);
  }

  let trazo = "";
  for (let posicion = 0; posicion < serie.length; posicion += 1) {
    trazo += `${posicion === 0 ? "M" : "L"}${x(serie[posicion].mae)} ${centroFila(posicion)}`;
  }
  crear("path", { d: trazo, class: "linea-serie" }, svg);

  for (let posicion = 0; posicion < serie.length; posicion += 1) {
    const punto = serie[posicion];
    const centroY = centroFila(posicion);
    const nombre = etiqueta(punto.modelo);
    if (estrecho) {
      escribir(svg, margen.izquierda, centroY - 14, nombre, "texto-eje");
    } else {
      escribir(svg, margen.izquierda - 8, centroY + 4, nombre, "texto-eje", "end");
    }
    const marcador = dibujarMarcador(svg, x(punto.mae), centroY, punto.conjunto);
    titular(
      marcador,
      t("graficos.d.punto", { modelo: nombre, mae: euros(punto.mae, actual), conjunto: t(`graficos.d.${punto.conjunto}`) }),
    );
    escribir(svg, x(punto.mae) + 10, centroY + 4, euros(punto.mae, actual), punto.conjunto === "test" ? "texto-marcado" : "texto-valor");
  }
}

// --- Entrada pública -------------------------------------------------------

// resultado: última respuesta de /api/v1/predict, o null si aún no hay.
export function dibujarGraficos(informe, resultado) {
  dibujarGraficoA(informe, resultado);
  dibujarGraficoB(informe, resultado);
  dibujarGraficoC(informe);
  dibujarGraficoD(informe);
}
