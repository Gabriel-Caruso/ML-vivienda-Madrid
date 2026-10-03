# Tasador de vivienda en Madrid

Servicio web que estima el precio de venta de una vivienda en Madrid con un modelo CatBoost ya entrenado. Proyecto de portfolio: la calidad de la arquitectura y del código es tan importante como que funcione.

## Origen
- Modelo entrenado en el proyecto final de ML del bootcamp (repo `Gabriel-Caruso/ML-idealista`), por Ramiro Caruso y Ana Manzanares. El EDA es de Ana; el preprocesado, el modelado y la optimización, de Ramiro.
- Existe un despliegue previo de referencia (`A-Manz/TCH-5-Despliegue`, rama develop). Este repo lo rehace desde cero con mejor arquitectura. No copies su estructura.

## El modelo (no se toca)
- Archivo: `models/catboost_madrid.joblib`.
- Es un `sklearn.compose.TransformedTargetRegressor` con `func=np.log1p` e `inverse_func=np.expm1` envolviendo un `CatBoostRegressor`. `predict()` devuelve euros directamente: no apliques ninguna transformación al resultado.
- Las columnas de entrada, su orden y sus nombres exactos son los de `model.regressor_.feature_names_`. Esa es la única fuente de verdad.
- Grupos de features:
  - Numéricas: `metros`, `baños_limpio`, `habitaciones_limpio`.
  - Categóricas nativas de CatBoost: `zona`, `tipo_inmueble`, `ascensor_limpio`, `localizacion_limpio`, `barrio`, `planta_limpio`.
  - Binarias (0/1): 7 `flag_*` y unos 55 `tag_*`.
- Reglas del preprocesado original que la API debe respetar:
  - `baños = 0` se convirtió en NaN en el entrenamiento. El modelo nunca vio un 0 en baños. `baños_limpio` es NaN en el 78 % de las filas de entrenamiento.
  - `habitaciones_limpio = 0` sí es válido (estudios).
  - Ambos admiten NaN; CatBoost lo gestiona de forma nativa.
  - Cada barrio pertenece a una sola zona (139 barrios, 21 zonas).
- Versiones del entrenamiento: catboost 1.2.10, scikit-learn 1.9.0, pandas 3.0.3, numpy 2.5.x. Python 3.14 (no confirmado al 100 %).

## Stack
- Python + FastAPI + Pydantic v2 + Uvicorn.
- uv para entorno y dependencias (`pyproject.toml` + `uv.lock`).
- pytest para tests. Ruff para lint y formato.
- GitHub Actions para integración continua (Ruff + pytest en cada push).
- Despliegue en Render (plan gratuito) configurado con `render.yaml`.
- Fase 2 (NO ahora): interfaz servida por la propia app FastAPI (Jinja2 + CSS + JS sin build), bilingüe español/inglés.

## Arquitectura
Una sola aplicación, un solo paquete Python, con capas. NUNCA crees carpetas `frontend/` y `backend/`: la interfaz será una capa más del paquete (`src/tasador/web/`).

```
tasador-madrid/
├── pyproject.toml
├── uv.lock
├── .python-version
├── render.yaml
├── README.md
├── .github/workflows/ci.yml
├── docs/DECISIONES.md
├── models/catboost_madrid.joblib
├── data/                      # datos locales de trabajo, en .gitignore
├── scripts/                   # utilidades de un solo uso (generar catálogo, fixtures)
├── src/tasador/
│   ├── main.py                # create_app(), lifespan: carga del modelo una sola vez
│   ├── config.py              # rutas, márgenes de error, umbrales
│   ├── api/v1/                # rutas: health, metadata, predict
│   ├── schemas/               # contratos Pydantic de entrada y salida
│   ├── services/predictor.py  # entrada -> DataFrame del modelo -> predicción
│   ├── domain/                # catálogo (zonas, barrios, tipos, plantas), grupos de tags, rangos válidos
│   └── web/                   # FASE 2. No crear nada aquí todavía.
└── tests/
    ├── fixtures/
    ├── unit/
    └── integration/
```

Principios:
- Las rutas solo reciben, validan y responden. La lógica vive en `services/` y el conocimiento del problema en `domain/`.
- El mapeo entre el contrato público de la API y los nombres de columnas del modelo está en un único sitio.
- La API está versionada (`/api/v1/...`). `/docs` (Swagger) se mantiene.
- Los errores se devuelven con códigos estables (por ejemplo `BARRIO_NOT_IN_ZONE`), no con frases. La interfaz los traducirá.
- No se guardan las peticiones de los usuarios. Solo logs técnicos.

## Contrato público
- Nombres de campos en inglés, snake_case y sin caracteres especiales (`bathrooms`, `rooms`, `district`, `neighbourhood`...). Internamente se mapean a las columnas del modelo.
- `bathrooms` y `rooms` son opcionales (null = desconocido). `bathrooms`, si se envía, debe ser >= 1.
- Todos los tags y flags son opcionales y valen 0 por defecto.
- La respuesta incluye el precio estimado, el margen de error aplicado y la horquilla resultante (mínimo y máximo).

## Calidad: obligatorio tras cada cambio
1. `uv run ruff format .`
2. `uv run ruff check .`
3. `uv run pytest`

No des una tarea por terminada si algo falla. Si un test falla y no sabes por qué, para y explícamelo; no lo "arregles" cambiando el test.

## Al terminar cada tarea, informa de
- Qué has cambiado y por qué.
- Resultado de Ruff y pytest.
- Decisiones añadidas a `docs/DECISIONES.md`.
- Dudas o incertidumbres pendientes.
- Mensaje de commit propuesto (no lo ejecutes).
