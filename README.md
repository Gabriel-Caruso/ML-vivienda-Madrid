# Tasador de vivienda en Madrid

Servicio web que estima el precio de venta de una vivienda en Madrid a partir de sus características. Devuelve un precio estimado y una horquilla basada en el error real del modelo en cada tramo de precio.

Tiene dos partes: una API REST hecha con FastAPI que sirve un modelo CatBoost ya entrenado, y una interfaz web bilingüe (español e inglés) con estética de terminal, hecha con HTML, CSS y JavaScript sin dependencias ni paso de build.

- **Web:** https://ml-vivienda-madrid-1.onrender.com
- **API:** https://ml-vivienda-madrid.onrender.com (documentación en `/docs`)

> No es una tasación oficial. Es una estimación orientativa a partir de anuncios publicados.

## Origen del modelo

El modelo es el resultado del proyecto final de Machine Learning del bootcamp, en el repositorio [Gabriel-Caruso/ML-idealista](https://github.com/Gabriel-Caruso/ML-idealista):

- **Datos:** [dataset de Kaggle](https://www.kaggle.com/datasets/fjcob1/idealista-madrid) con anuncios de viviendas en venta en Madrid publicados en Idealista en 2025.
- **Análisis exploratorio (EDA):** Ana Manzanares.
- **Preprocesado, modelado y optimización:** Ramiro Caruso.
- **Modelo:** `CatBoostRegressor` optimizado con Optuna y entrenado sobre el logaritmo del precio (`TransformedTargetRegressor` con `log1p`/`expm1`). Usa 69 variables: superficie, baños, habitaciones, distrito, barrio, tipo de inmueble, ascensor, exterior/interior, planta y 60 indicadores binarios extraídos del anuncio.

### Métricas sobre el conjunto de test

| Métrica | Valor |
|---|---:|
| MAE | 180.710 € |
| RMSE | 439.765 € |
| R² | 0,863 |

### Horquilla de precio

El margen de la horquilla es el error relativo del modelo en el tramo de precio en que cae la estimación:

| Precio estimado | Error relativo aplicado |
|---|---:|
| Menos de 250.000 € | 17 % |
| 250.000 - 435.360 € | 15 % |
| 435.360 - 835.600 € | 16 % |
| 835.600 - 1.490.000 € | 15 % |
| 1.490.000 € o más | 24 % |

## Ejecutar en local

Requisitos: [uv](https://docs.astral.sh/uv/). uv instala por su cuenta Python 3.14.4, la versión fijada en `.python-version`.

```bash
git clone https://github.com/Gabriel-Caruso/ML-vivienda-Madrid.git
cd ML-vivienda-Madrid
uv sync
uv run uvicorn --factory tasador.main:create_app --reload
```

La web queda en `http://127.0.0.1:8000`, la API en `http://127.0.0.1:8000/api/v1/` y la documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`. En local la propia app sirve la web, así que basta un comando.

Comprobaciones de calidad, las mismas que ejecuta la integración continua:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

## Interfaz web

Vive en `src/tasador/web/` como archivos estáticos: `index.html`, `css/`, `js/` (módulos ES), `i18n/` (diccionarios `es.json` y `en.json`), `datos/` (JSON precalculados), `fuentes/` y `config.js`.

- **Formulario:** distrito y barrio como desplegables con búsqueda (el barrio solo ofrece los del distrito elegido), "no lo sé" en habitaciones y baños, planta, ascensor y localización ocultos en casas y chalets, y "más opciones" con las casillas de características y situación legal. Valida en el navegador con las mismas reglas y códigos de error que la API.
- **Arranque:** al abrir la página llama a `/api/v1/health` para que la API despierte mientras se rellena el formulario. El formulario funciona desde el primer momento con el catálogo estático (`datos/catalogo.json`, idéntico a `/api/v1/metadata`).
- **Resultado:** precio redondeado a miles, margen y horquilla, y dos gráficos (error relativo por tramo de precio, y precio real frente a predicho en test) con la estimación marcada.
- **Sobre el modelo:** texto con las cifras reales del informe del modelo, importancia de variables y MAE de cada paso del modelado.
- **Fondo:** un "holograma CRT" del árbol 0 real del modelo, con los cortes de cada nivel. Quieto en reposo; al calcular se ilumina de arriba abajo hasta la salida "-> PREDICCIÓN". Sin barrido si el sistema pide movimiento reducido.
- **Sin terceros:** sin analítica, cookies ni peticiones externas; las fuentes están alojadas en el proyecto con sus licencias.

La URL de la API se lee de `config.js`. En el repositorio está vacía (mismo origen, como en local) y el Static Site de Render la escribe en su build a partir de la variable `API_BASE_URL`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Interfaz web (archivos de `src/tasador/web/`) |
| GET | `/api/v1/` | Nombre, versión y enlaces de la API |
| GET | `/api/v1/health` | Estado del servicio y del modelo |
| GET | `/api/v1/metadata` | Catálogo para construir el formulario |
| POST | `/api/v1/predict` | Precio estimado con su horquilla |
| GET | `/docs` | Documentación interactiva |

### `GET /api/v1/health`

```json
{"status": "ok", "model_loaded": true}
```

Devuelve 503 si el modelo no está cargado. Admite también `HEAD`, como `/`, para monitores de disponibilidad.

### `GET /api/v1/metadata`

Devuelve todo lo necesario para construir el formulario, con etiquetas en español e inglés:

- campos, con su obligatoriedad y su rango;
- distritos con sus barrios, tipos de inmueble, ascensor, exterior/interior y plantas;
- los dos grupos de "más opciones": características de la vivienda, y situación legal.

Ejemplo de un distrito:

```json
{
  "value": "centro",
  "label": {"es": "Centro", "en": "Centro"},
  "neighbourhoods": ["Chueca-Justicia", "Huertas-Cortes", "Lavapiés-Embajadores", "Malasaña-Universidad", "Palacio", "Sol"]
}
```

### `POST /api/v1/predict`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "area_m2": 85,
    "bathrooms": 2,
    "rooms": 3,
    "district": "chamberi",
    "neighbourhood": "Trafalgar",
    "property_type": "Piso",
    "lift": "S",
    "position": "EXTERIOR",
    "floor": "3ª",
    "options": ["terrace", "renovated"]
  }'
```

```json
{"estimated_price": 816655, "error_margin": 0.16, "price_min": 685990, "price_max": 947320}
```

| Campo | Obligatorio | Valores |
|---|---|---|
| `area_m2` | sí | entero, 10-3100 |
| `district` | sí | distrito del catálogo (`/api/v1/metadata`) |
| `neighbourhood` | sí | barrio que pertenezca al distrito |
| `property_type` | sí | tipo del catálogo (`Piso`, `Ático`, `Chalet adosado`...) |
| `bathrooms` | no | entero, 1-7, o `null` si se desconoce |
| `rooms` | no | entero, 0-20 (0 en estudios), o `null` |
| `lift` | no | `S`, `N` o `null` |
| `position` | no | `EXTERIOR`, `INTERIOR` o `null` |
| `floor` | no | planta del catálogo (`BAJO`, `3ª`...) o `null` |
| `options` | no | lista de claves de "más opciones"; las no enviadas valen 0 |

Los precios se devuelven en euros enteros.

### Errores

Los errores se devuelven con códigos estables, no con frases, para que la interfaz los traduzca. Siempre llegan como una lista:

```json
{
  "errors": [
    {
      "code": "BARRIO_NOT_IN_ZONE",
      "field": "neighbourhood",
      "message": "Neighbourhood 'Trafalgar' does not belong to district 'centro'",
      "params": {"neighbourhood": "Trafalgar", "district": "centro"}
    }
  ]
}
```

| Código | Estado | Significado |
|---|---|---|
| `INVALID_JSON` | 422 / 400 | El cuerpo no es JSON válido (400 si ni siquiera se puede leer, por ejemplo texto que no es UTF-8) |
| `FIELD_REQUIRED` | 422 | Falta un campo obligatorio |
| `UNKNOWN_FIELD` | 422 | Campo que no forma parte del contrato |
| `INVALID_TYPE` | 422 | Tipo incorrecto (por ejemplo, `"85"` en lugar de `85`) |
| `INVALID_VALUE` | 422 | Valor no válido sin código más específico |
| `OUT_OF_RANGE` | 422 | Número fuera de rango (`params`: `min`, `max`) |
| `BATHROOMS_ZERO` | 422 | `bathrooms` vale 0; si se desconoce, enviar `null` |
| `VALUE_NOT_IN_CATALOG` | 422 | Valor que no está en el catálogo |
| `BARRIO_NOT_IN_ZONE` | 422 | El barrio no pertenece al distrito |
| `UNKNOWN_OPTION` | 422 | Clave de "más opciones" desconocida |
| `NOT_FOUND` | 404 | Ruta inexistente |
| `METHOD_NOT_ALLOWED` | 405 | Método no permitido en esa ruta (cabecera `Allow` con los válidos) |
| `MODEL_NOT_LOADED` | 503 | El modelo no está cargado |
| `INTERNAL_ERROR` | 500 | Error interno |

## Despliegue

Se despliega en [Render](https://render.com) como dos servicios gratuitos. `render.yaml` recoge su configuración; en el panel se introdujeron los mismos valores.

**Web Service (API)**

| Ajuste | Valor |
|---|---|
| Runtime / plan / región | Python 3 / Free / Frankfurt |
| Build Command | `uv sync --locked --no-dev` |
| Start Command | `uv run --no-sync uvicorn --factory tasador.main:create_app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/api/v1/health` |
| Auto-Deploy | After CI Checks Pass |
| `UV_VERSION` | `0.12.23` |
| `ALLOWED_ORIGINS` | `https://ml-vivienda-madrid-1.onrender.com` (orígenes que pueden llamar a la API desde el navegador, separados por comas) |

**Static Site (web)**

| Ajuste | Valor |
|---|---|
| Publish Directory | `src/tasador/web` |
| Build Command | `printf 'window.TASADOR_CONFIG = { apiBaseUrl: "%s", portfolioUrl: "%s" };\n' "$API_BASE_URL" "$PORTFOLIO_URL" > src/tasador/web/config.js` |
| `API_BASE_URL` | `https://ml-vivienda-madrid.onrender.com` (sin barra final) |
| `PORTFOLIO_URL` | opcional; mientras esté vacía, el enlace al portfolio no aparece |
| Header | ruta `/*`, `Cache-Control: no-cache`, para que el navegador no use archivos antiguos tras un despliegue |

Python sale de `.python-version` y Render activa uv al encontrar `uv.lock`.

**Arranque en frío:** en el plan gratuito, Render detiene la API tras 15 minutos sin tráfico. La primera petición después de ese tiempo puede tardar alrededor de un minuto mientras el servicio arranca y carga el modelo. La web lo indica en su registro de arranque y deja en cola la estimación hasta que la API responde.

## Estructura

```
src/tasador/
├── main.py              # create_app(): rutas, errores y carga del modelo en el lifespan
├── config.py            # rutas y tramos de la horquilla
├── api/                 # rutas HTTP (versionadas en /api/v1), web estática y traducción de errores
├── schemas/             # contratos Pydantic de entrada y salida
├── services/            # petición -> fila del modelo -> predicción; horquilla; metadata
├── domain/              # catálogo, reglas del preprocesado, rangos, opciones y etiquetas
└── web/                 # interfaz web estática (HTML, CSS, JS, i18n, datos, fuentes)
scripts/                 # generación de catálogos, fixtures, datos de gráficos, árbol e imagen
tests/                   # tests unitarios, de integración y de referencia
docs/DECISIONES.md       # registro de decisiones técnicas
```

Los datos generados están versionados y solo hace falta regenerarlos si cambian los datos o el dominio. Todos los scripts son deterministas y hay tests que comprueban que los archivos versionados coinciden con lo que generan.

| Script | Genera | Necesita `data/` |
|---|---|---|
| `build_catalog.py` | `src/tasador/domain/catalogo.json` | sí |
| `build_fixtures.py` | `tests/fixtures/filas_referencia.json` | sí |
| `build_model_report.py` | `web/datos/informe_modelo.json` (métricas y gráficos) | sí |
| `build_web_catalog.py` | `web/datos/catalogo.json` | no |
| `export_tree.py` | `web/datos/arbol.json` (árbol del fondo) | no |
| `build_og_image.py` | `web/og.png` (imagen para compartir) | no |

Los que necesitan datos usan `train.csv` y `test.csv` de `src/data_sample/` del repositorio de entrenamiento, copiados en `data/` (excluida de git). Se ejecutan con `uv run python scripts/<script>`.

Un test de referencia comprueba que, para 20 viviendas reales, la API reproduce exactamente la predicción que da el modelo sobre la fila procesada en el notebook original.

## Limitaciones

- **Fecha de los datos:** el modelo se entrenó con anuncios de 2025. No recoge la evolución posterior del mercado.
- **Precio de anuncio:** estima el precio que se pide en un anuncio, no el precio final de venta ni el valor de tasación.
- **Cobertura:** solo Madrid capital (21 distritos y 139 barrios, según la división de Idealista).
- **Error variable:** el error crece en las viviendas de más de 1.490.000 € (24 %). La horquilla lo refleja.
- **No es una tasación oficial:** no sustituye a una tasación homologada.

## Autoría

Modelo de Ramiro Caruso y Ana Manzanares.

- **Ana Manzanares:** análisis exploratorio de datos (EDA).
- **Ramiro Caruso:** preprocesado, modelado y optimización, y este servicio web.

Fuentes: [IBM VGA 9x16](https://int10h.org/oldschool-pc-fonts/) (VileR, CC BY-SA 4.0) e [IBM Plex Mono](https://github.com/IBM/plex) (SIL OFL 1.1).
