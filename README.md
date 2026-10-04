# Tasador de vivienda en Madrid

Servicio web que estima el precio de venta de una vivienda en Madrid a partir de sus características. Devuelve un precio estimado y una horquilla basada en el error real del modelo en cada tramo de precio.

Es una API REST hecha con FastAPI que sirve un modelo CatBoost ya entrenado. La interfaz web, bilingüe en español e inglés, llegará en una segunda fase servida por la propia aplicación.

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

La API queda en `http://127.0.0.1:8000` y la documentación interactiva (Swagger) en `http://127.0.0.1:8000/docs`.

Comprobaciones de calidad, las mismas que ejecuta la integración continua:

```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Nombre, versión y enlaces |
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
- los dos grupos de "más opciones": características de la vivienda, y situación legal y del anuncio.

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

El servicio se despliega en [Render](https://render.com) con el blueprint `render.yaml`:

- **Plan:** gratuito, en la región de Fráncfort.
- **Build y arranque:** `uv sync --locked --no-dev` y `uvicorn --factory tasador.main:create_app`.
- **Health check:** en `/api/v1/health`.
- **Despliegue automático:** solo cuando la integración continua de GitHub pasa.

**Arranque en frío:** en el plan gratuito, Render detiene el servicio tras 15 minutos sin tráfico. La primera petición después de ese tiempo puede tardar alrededor de un minuto mientras el servicio arranca y carga el modelo. Las siguientes responden con normalidad.

## Estructura

```
src/tasador/
├── main.py              # create_app(): rutas, errores y carga del modelo en el lifespan
├── config.py            # rutas y tramos de la horquilla
├── api/                 # rutas HTTP (versionadas en /api/v1) y traducción de errores
├── schemas/             # contratos Pydantic de entrada y salida
├── services/            # petición -> fila del modelo -> predicción; horquilla; metadata
└── domain/              # catálogo, reglas del preprocesado, rangos, opciones y etiquetas
scripts/                 # generación del catálogo y de los fixtures, verificación del modelo
tests/                   # tests unitarios, de integración y de referencia
docs/DECISIONES.md       # registro de decisiones técnicas
```

El catálogo (`src/tasador/domain/catalogo.json`) y los fixtures de test (`tests/fixtures/`) están versionados. Solo hace falta regenerarlos si cambian los datos. Para ello se copian `train.csv` y `test.csv` de `src/data_sample/` del repositorio de entrenamiento a `data/` (excluida de git) y se ejecuta:

```bash
uv run python scripts/build_catalog.py
uv run python scripts/build_fixtures.py
```

Un test de referencia comprueba que, para 20 viviendas reales, la API reproduce exactamente la predicción que da el modelo sobre la fila procesada en el notebook original.

## Limitaciones

- **Fecha de los datos:** el modelo se entrenó con anuncios de 2025. No recoge la evolución posterior del mercado.
- **Precio de anuncio:** estima el precio que se pide en un anuncio, no el precio final de venta ni el valor de tasación.
- **Cobertura:** solo Madrid capital (21 distritos y 139 barrios, según la división de Idealista).
- **Error variable:** el error crece en las viviendas de más de 1.490.000 € (24 %). La horquilla lo refleja.
- **No es una tasación oficial:** no sustituye a una tasación homologada.

## Autoría

Ramiro Caruso y Ana Manzanares.

- **Ana Manzanares:** análisis exploratorio de datos (EDA).
- **Ramiro Caruso:** preprocesado, modelado y optimización.
