// Cliente de la API. La URL base sale de config.js: vacía en local (mismo origen)
// y la del Web Service en producción.

const configuracion = window.TASADOR_CONFIG || { apiBaseUrl: "" };

// La primera petición a una instancia dormida de Render tarda en torno a un
// minuto: el tiempo de espera de health es largo a propósito.
const ESPERA_SALUD_MS = 90000;
const ESPERA_PREDICCION_MS = 60000;

export class ErrorDeRed extends Error {}

function url(ruta) {
  return `${configuracion.apiBaseUrl}${ruta}`;
}

async function pedir(ruta, opciones, esperaMs) {
  try {
    return await fetch(url(ruta), { ...opciones, signal: AbortSignal.timeout(esperaMs) });
  } catch (error) {
    throw new ErrorDeRed(error.message);
  }
}

// true si la API responde con el modelo cargado; false si responde pero no está lista.
export async function comprobarSalud() {
  const respuesta = await pedir("/api/v1/health", { method: "GET" }, ESPERA_SALUD_MS);
  if (!respuesta.ok) {
    return false;
  }
  const cuerpo = await respuesta.json();
  return cuerpo.model_loaded === true;
}

// Devuelve { ok, estado, cuerpo }. Los errores de la API llegan como
// { errors: [{ code, field, message, params }] }.
export async function predecir(peticion) {
  const respuesta = await pedir(
    "/api/v1/predict",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(peticion),
    },
    ESPERA_PREDICCION_MS,
  );
  let cuerpo = null;
  try {
    cuerpo = await respuesta.json();
  } catch (error) {
    cuerpo = null;
  }
  return { ok: respuesta.ok, estado: respuesta.status, cuerpo };
}

export function urlPortfolio() {
  return configuracion.portfolioUrl || "";
}
