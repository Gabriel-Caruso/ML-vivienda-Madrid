// Formulario de tasación construido a partir de datos/catalogo.json (= GET /api/v1/metadata).
// La validación usa las mismas reglas y los mismos códigos de error que la API.

import { Combobox } from "./combobox.js";
import { etiqueta, t } from "./i18n.js";

const CAMPOS_NUMERICOS = ["area_m2", "rooms", "bathrooms"];
const CAMPOS_DESCONOCIBLES = ["rooms", "bathrooms"];

let catalogo = null;
let comboDistrito = null;
let comboBarrio = null;
const casillas = [];
// Errores mostrados ahora mismo; se redibujan al cambiar de idioma
let erroresVigentes = [];

function elemento(id) {
  return document.getElementById(id);
}

function campoPorNombre(nombre) {
  for (const campo of catalogo.fields) {
    if (campo.name === nombre) {
      return campo;
    }
  }
  return null;
}

function distritoPorValor(valor) {
  for (const distrito of catalogo.districts) {
    if (distrito.value === valor) {
      return distrito;
    }
  }
  return null;
}

function tipoPorValor(valor) {
  for (const tipo of catalogo.property_types) {
    if (tipo.value === valor) {
      return tipo;
    }
  }
  return null;
}

function esCasa() {
  const tipo = tipoPorValor(elemento("campo-property_type").value);
  return tipo !== null && tipo.is_house;
}

// --- Construcción -------------------------------------------------------

function rellenarSelect(select, opciones, textoVacio) {
  const elegido = select.value;
  select.replaceChildren();
  const vacia = document.createElement("option");
  vacia.value = "";
  vacia.textContent = textoVacio;
  select.append(vacia);
  for (const opcion of opciones) {
    const nueva = document.createElement("option");
    nueva.value = opcion.value;
    nueva.textContent = etiqueta(opcion.label);
    select.append(nueva);
  }
  select.value = elegido;
}

function opcionesDeBarrio() {
  const distrito = distritoPorValor(comboDistrito.valor());
  if (distrito === null) {
    return [];
  }
  const opciones = [];
  for (const barrio of distrito.neighbourhoods) {
    opciones.push({ valor: barrio, texto: barrio });
  }
  return opciones;
}

function alCambiarDistrito() {
  quitarErroresDeCampo("district");
  comboBarrio.establecerOpciones(opcionesDeBarrio());
  comboBarrio.habilitar(comboDistrito.valor() !== "");
  actualizarTextosCombos();
}

function alCambiarTipo() {
  const casa = esCasa();
  elemento("campos-edificio").hidden = casa;
  elemento("aviso-casa").hidden = !casa;
}

function alCambiarNoLoSe(nombre) {
  const marcado = elemento(`no-sabe-${nombre}`).checked;
  const entrada = elemento(`campo-${nombre}`);
  entrada.disabled = marcado;
  if (marcado) {
    entrada.value = "";
  }
}

function construirGrupos() {
  const contenedor = elemento("grupos-opciones");
  contenedor.replaceChildren();
  casillas.length = 0;
  for (const grupo of catalogo.option_groups) {
    const conjunto = document.createElement("fieldset");
    const leyenda = document.createElement("legend");
    leyenda.dataset.grupo = grupo.key;
    conjunto.append(leyenda);
    for (const opcion of grupo.options) {
      const etiquetaCasilla = document.createElement("label");
      const casilla = document.createElement("input");
      casilla.type = "checkbox";
      casilla.name = "options";
      casilla.value = opcion.key;
      const texto = document.createElement("span");
      texto.dataset.opcion = opcion.key;
      etiquetaCasilla.append(casilla, " ", texto);
      conjunto.append(etiquetaCasilla);
      casillas.push(casilla);
    }
    contenedor.append(conjunto);
  }
}

export function construirFormulario(datosCatalogo) {
  catalogo = datosCatalogo;
  comboDistrito = new Combobox(elemento("combobox-district"), "district", alCambiarDistrito);
  comboBarrio = new Combobox(elemento("combobox-neighbourhood"), "neighbourhood", function () {
    quitarErroresDeCampo("neighbourhood");
  });
  comboBarrio.habilitar(false);
  elemento("campo-property_type").addEventListener("change", alCambiarTipo);
  for (const nombre of CAMPOS_DESCONOCIBLES) {
    elemento(`no-sabe-${nombre}`).addEventListener("change", function () {
      alCambiarNoLoSe(nombre);
    });
  }
  for (const nombre of CAMPOS_NUMERICOS) {
    const rango = campoPorNombre(nombre).range;
    elemento(`campo-${nombre}`).min = String(rango.min);
    elemento(`campo-${nombre}`).max = String(rango.max);
  }
  construirGrupos();
  traducirFormulario();
  elemento("formulario").addEventListener("input", alModificarCampo);
  elemento("formulario").addEventListener("change", alModificarCampo);
}

// --- Textos según el idioma ----------------------------------------------

function actualizarTextosCombos() {
  comboDistrito.establecerTextos(t("formulario.buscar"), t("formulario.sin_coincidencias"));
  const marcadorBarrio =
    comboDistrito.valor() === "" ? t("formulario.elige_distrito") : t("formulario.buscar");
  comboBarrio.establecerTextos(marcadorBarrio, t("formulario.sin_coincidencias"));
}

export function traducirFormulario() {
  for (const etiquetaCampo of document.querySelectorAll("[data-etiqueta-campo]")) {
    etiquetaCampo.textContent = etiqueta(campoPorNombre(etiquetaCampo.dataset.etiquetaCampo).label);
  }
  for (const nombre of CAMPOS_NUMERICOS) {
    const rango = campoPorNombre(nombre).range;
    elemento(`rango-${nombre}`).textContent = t("formulario.rango", rango);
  }
  const distritos = [];
  for (const distrito of catalogo.districts) {
    distritos.push({ valor: distrito.value, texto: etiqueta(distrito.label) });
  }
  comboDistrito.establecerOpciones(distritos);
  comboBarrio.establecerOpciones(opcionesDeBarrio());
  actualizarTextosCombos();

  rellenarSelect(elemento("campo-property_type"), catalogo.property_types, t("formulario.elegir"));
  rellenarSelect(elemento("campo-floor"), catalogo.floors, t("formulario.no_indicado"));
  rellenarSelect(elemento("campo-lift"), catalogo.lift, t("formulario.no_indicado"));
  rellenarSelect(elemento("campo-position"), catalogo.position, t("formulario.no_indicado"));

  for (const grupo of catalogo.option_groups) {
    document.querySelector(`[data-grupo="${grupo.key}"]`).textContent = etiqueta(grupo.label);
    for (const opcion of grupo.options) {
      document.querySelector(`[data-opcion="${opcion.key}"]`).textContent = etiqueta(opcion.label);
    }
  }
}

// --- Lectura y validación ------------------------------------------------

function leerEntero(nombre, errores) {
  const entrada = elemento(`campo-${nombre}`);
  const texto = entrada.value.trim();
  if (texto === "") {
    return null;
  }
  if (!/^-?\d+$/.test(texto)) {
    errores.push({ code: "INVALID_TYPE", field: nombre, params: {} });
    return null;
  }
  return Number(texto);
}

function comprobarRango(nombre, valor, errores) {
  const rango = campoPorNombre(nombre).range;
  if (valor !== null && (valor < rango.min || valor > rango.max)) {
    errores.push({ code: "OUT_OF_RANGE", field: nombre, params: rango });
  }
}

function valorOpcional(nombre) {
  const valor = elemento(`campo-${nombre}`).value;
  return valor === "" ? null : valor;
}

// Devuelve { peticion, errores }. Si hay errores, la petición no debe enviarse.
export function leerPeticion() {
  const errores = [];

  const distrito = comboDistrito.valor();
  if (distrito === "") {
    errores.push({ code: "FIELD_REQUIRED", field: "district", params: {} });
  }
  const barrio = comboBarrio.valor();
  if (barrio === "") {
    errores.push({ code: "FIELD_REQUIRED", field: "neighbourhood", params: {} });
  }
  const tipo = elemento("campo-property_type").value;
  if (tipo === "") {
    errores.push({ code: "FIELD_REQUIRED", field: "property_type", params: {} });
  }

  const metros = leerEntero("area_m2", errores);
  if (metros === null && elemento("campo-area_m2").value.trim() === "") {
    errores.push({ code: "FIELD_REQUIRED", field: "area_m2", params: {} });
  }
  comprobarRango("area_m2", metros, errores);

  let habitaciones = null;
  if (!elemento("no-sabe-rooms").checked) {
    habitaciones = leerEntero("rooms", errores);
    comprobarRango("rooms", habitaciones, errores);
  }

  let banos = null;
  if (!elemento("no-sabe-bathrooms").checked) {
    banos = leerEntero("bathrooms", errores);
    if (banos === 0) {
      errores.push({ code: "BATHROOMS_ZERO", field: "bathrooms", params: {} });
    } else {
      comprobarRango("bathrooms", banos, errores);
    }
  }

  // En casas y chalets estos campos no aplican: se envían como null y la API
  // los convierte en NO_APLICA, como en el entrenamiento.
  const casa = esCasa();
  const opciones = [];
  for (const casilla of casillas) {
    if (casilla.checked) {
      opciones.push(casilla.value);
    }
  }

  const peticion = {
    area_m2: metros,
    bathrooms: banos,
    rooms: habitaciones,
    district: distrito,
    neighbourhood: barrio,
    property_type: tipo,
    lift: casa ? null : valorOpcional("lift"),
    position: casa ? null : valorOpcional("position"),
    floor: casa ? null : valorOpcional("floor"),
    options: opciones,
  };
  return { peticion, errores };
}

// --- Errores -------------------------------------------------------------

export function limpiarErrores() {
  erroresVigentes = [];
  borrarErroresMostrados();
}

function borrarErroresMostrados() {
  const resumen = elemento("errores-formulario");
  resumen.hidden = true;
  resumen.replaceChildren();
  for (const parrafo of document.querySelectorAll(".error-campo")) {
    parrafo.hidden = true;
    parrafo.textContent = "";
  }
  for (const marcado of document.querySelectorAll("[aria-invalid]")) {
    marcado.removeAttribute("aria-invalid");
  }
}

function textoError(error) {
  return `ERROR: ${t(`errores.${error.code}`, error.params || {})}`;
}

// Muestra errores con códigos estables (del cliente o de la API) junto a su campo.
// Los que no tienen campo conocido van al resumen del formulario.
export function mostrarErrores(errores, enfocar = true) {
  erroresVigentes = errores;
  borrarErroresMostrados();
  if (errores.length === 0) {
    return;
  }
  const resumen = elemento("errores-formulario");
  const lineasResumen = [];
  let hayErroresDeCampo = false;
  let primero = null;
  for (const error of errores) {
    const parrafo = error.field ? elemento(`error-${error.field}`) : null;
    if (parrafo) {
      hayErroresDeCampo = true;
      parrafo.textContent = textoError(error);
      parrafo.hidden = false;
      const entrada = elemento(`campo-${error.field}`);
      if (entrada) {
        entrada.setAttribute("aria-invalid", "true");
        if (primero === null) {
          primero = entrada;
        }
      }
    } else {
      lineasResumen.push(textoError(error));
    }
  }
  if (hayErroresDeCampo) {
    lineasResumen.unshift(t("formulario.hay_errores"));
  }
  for (const linea of lineasResumen) {
    const parrafo = document.createElement("p");
    parrafo.textContent = linea;
    resumen.append(parrafo);
  }
  resumen.hidden = false;
  if (enfocar && primero !== null) {
    primero.focus();
  }
}

export function redibujarErrores() {
  mostrarErrores(erroresVigentes, false);
}

// Al corregir un campo desaparece su error, sin esperar al siguiente envío.
function quitarErroresDeCampo(nombre) {
  const restantes = [];
  let habiaErrores = false;
  for (const error of erroresVigentes) {
    if (error.field === nombre) {
      habiaErrores = true;
    } else {
      restantes.push(error);
    }
  }
  if (habiaErrores) {
    mostrarErrores(restantes, false);
  }
}

// Campo del contrato al que pertenece el elemento modificado
function campoDeElemento(destino) {
  if (destino.name === "options") {
    return "options";
  }
  if (destino.id.startsWith("no-sabe-")) {
    return destino.id.slice("no-sabe-".length);
  }
  if (destino.id.startsWith("campo-")) {
    return destino.id.slice("campo-".length);
  }
  return null;
}

function alModificarCampo(evento) {
  const nombre = campoDeElemento(evento.target);
  if (nombre !== null) {
    quitarErroresDeCampo(nombre);
  }
}
