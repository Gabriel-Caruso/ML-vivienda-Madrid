# Registro de decisiones técnicas

Cada entrada recoge qué se decidió, por qué y qué alternativas se descartaron.
Estado: **aprobada** (confirmada por el responsable del proyecto) o **pendiente de confirmar**.

---

## D-001. Python 3.14.4 en local, CI y Render

- **Estado:** aprobada.
- **Qué:** `.python-version` con `3.14.4` y `requires-python = "==3.14.*"`.
- **Por qué:** los notebooks del entrenamiento registran Python 3.14.4 en sus metadatos. Hay ruedas cp314 de catboost 1.2.10, scikit-learn 1.9.0, pandas 3.0.3 y numpy 2.5.1 para Windows x64 y Linux x86_64 (comprobado en PyPI). Render admite Python 3.14 (su versión por defecto desde febrero de 2026 es 3.14.3) y lee `.python-version`.
- **Alternativas descartadas:** Python 3.13, innecesario porque 3.14 es viable en todas partes. Fijar la versión en Render con la variable `PYTHON_VERSION`: duplicaría la fuente de verdad que ya es `.python-version`, que también usa uv.
- **Fuentes:** https://render.com/docs/python-version

## D-002. Versiones exactas en las librerías del modelo; cota inferior en la capa web

- **Estado:** aprobada.
- **Qué:** `catboost==1.2.10`, `scikit-learn==1.9.0`, `pandas==3.0.3`, `numpy==2.5.1`, `joblib==1.5.3` (las del `requirements.txt` del entrenamiento). FastAPI, Pydantic y Uvicorn con `>=` y versión exacta fijada por `uv.lock`.
- **Por qué:** el modelo está serializado con esas versiones; cambiarlas puede romper la carga o alterar predicciones. La capa web no afecta al modelo y conviene poder actualizarla con `uv lock --upgrade-package`.
- **Alternativas descartadas:** fijar también las dependencias indirectas (scipy, threadpoolctl...) a las del entrenamiento. No forman parte del objeto serializado y la carga y la predicción no dan avisos; además `uv.lock` ya las fija. Diferencias actuales: scipy 1.18.1 (entrenamiento 1.18.0), threadpoolctl 3.7.0 (3.6.0), plotly 7.1.0 (6.9.0).
- **Pydantic** se declara explícitamente aunque llegue con FastAPI, porque el código lo importa directamente.

## D-003. Gestión del proyecto con uv y backend de build `uv_build`

- **Estado:** aprobada.
- **Qué:** proyecto empaquetado (`src/tasador`) con `uv_build`, `module-name = "tasador"`. Dependencias de desarrollo en `[dependency-groups] dev`: ruff, pytest y httpx.
- **Por qué:** `uv_build` es el backend por defecto de `uv init --package` y no añade herramientas ajenas al stack. El nombre del módulo difiere del nombre del proyecto (`tasador-madrid`), por eso se indica `module-name`. `uv sync` instala el paquete en modo editable, de modo que `tasador.config` resuelve rutas respecto al repositorio.
- **httpx:** lo necesita `fastapi.testclient.TestClient`. Aprobado expresamente.
- **Alternativas descartadas:** hatchling o setuptools (dependencia de build adicional sin ventaja aquí); layout plano sin `src/` (permite importar el código sin instalarlo y oculta errores de empaquetado).
- **Fuente:** https://docs.astral.sh/uv/concepts/build-backend/

## D-004. Rutas calculadas desde `config.py`

- **Estado:** aprobada.
- **Qué:** `RAIZ_PROYECTO = Path(__file__).resolve().parents[2]` y `RUTA_MODELO` derivada de ella.
- **Por qué:** las rutas no dependen del directorio desde el que se lanza el proceso.
- **Limitación conocida:** depende de que el paquete se ejecute desde el repositorio (instalación editable), que es como lo hacen `uv sync`, la CI y Render. Si algún día se instalara como rueda, habría que mover el modelo dentro del paquete.
- **Alternativa descartada:** `importlib.resources` con el modelo dentro del paquete: contradice la estructura acordada (`models/` en la raíz).

## D-005. Ruff y pytest configurados en `pyproject.toml`

- **Estado:** aprobada.
- **Qué:** Ruff con longitud de línea 100, comillas dobles y reglas `E, W, F, I, UP, B, SIM, PTH, T20, RUF`. `PTH` obliga a usar pathlib y `T20` prohíbe `print` en el paquete (en `scripts/` se permite porque informan por consola). pytest con `filterwarnings = ["error"]`.
- **Por qué:** las reglas reflejan el estilo del proyecto (pathlib, sin prints de depuración). Convertir avisos en errores hace que un `InconsistentVersionWarning` de scikit-learn al cargar el modelo rompa los tests en vez de pasar desapercibido.
- **Alternativa descartada:** configuración por defecto de Ruff (solo `E` y `F`): no detecta el uso de `os.path` ni los `print`.

## D-006. `.gitignore`: datos locales y copias del modelo

- **Estado:** aprobada.
- **Qué:** se ignoran `data/` y `models/*.pkl`. Solo se versiona `models/catboost_madrid.joblib`.
- **Por qué:** los CSV de entrenamiento y otras copias del modelo no deben subirse.
- **Alternativa descartada:** ignorar solo `data/`: una copia del modelo colocada por error en `models/` acabaría en el repositorio.

## D-007. El joblib es el modelo de referencia; el pkl es otro modelo

- **Estado:** aprobada (el joblib ya era el modelo designado). Hallazgo informado.
- **Qué se comprobó (`scripts/verify_model.py`):** el joblib carga y predice sin avisos con las versiones fijadas. El pkl de `ML-idealista/src/models/` **no es el mismo modelo**: espera 70 columnas (incluye `tag_seguridad`) frente a 69, y el orden de 29 posiciones difiere. Los hiperparámetros coinciden.
- **Interpretación:** el pkl se entrenó sobre una versión distinta de `train.csv`. En el `train.csv` actual la etiqueta `SEGURIDAD` aparece 98 veces (umbral: 100) y el orden de frecuencias reproduce exactamente el de las columnas del joblib, no el del pkl. El joblib es, por tanto, coherente con los datos disponibles para catálogo y fixtures.
- **Consecuencia:** el pkl no se usa en nada. No se compararon predicciones porque las entradas no son compatibles.

## D-008. La reconstrucción de los tags vive en `scripts/`, no en el paquete

- **Estado:** aprobada.
- **Qué:** `scripts/preprocesado_original.py` replica el código del notebook que genera las columnas `tag_*` desde la columna `tags` en bruto (frecuencia >= 100 en train, `str.contains(..., regex=False)`).
- **Por qué:** solo lo necesitan los scripts (verificación, fixtures). La API recibe los tags ya como 0/1; meter el parseo de texto en `domain/` sería código muerto en producción.
- **Comprobado:** la reconstrucción produce las 53 columnas `tag_*` del modelo, en el mismo orden. Los guiones bajos de `tag_solo_particulares` y `tag_abstenerse_agencias` vienen de las etiquetas en bruto, no de una transformación.

## D-009. Memoria en ejecución

- **Estado:** informativo.
- **Medición (Windows, RSS):** 45 MiB el intérprete, 161 MiB tras importar catboost, scikit-learn, pandas y FastAPI, 192 MiB con el modelo cargado.
- **Implicación:** cabe en una instancia de 512 MB. La RAM del plan gratuito de Render no aparece en la documentación consultada: verificar en el panel al desplegar. En Linux la cifra puede variar.

---

## Decisiones aprobadas para pasos siguientes

- **Grupos de tags (paso 2):** "Características de la vivienda" (terraza, balcones, patio, jardín, piscina, parcela, vistas, garaje, armarios, calefacción, amueblada, equipada, electrodomésticos, portero, suite, reformado, reformada, estrenar, nuevo, reformar, urbanización, metro, parque, loft) y "Situación legal y del anuncio" (okupada, nuda propiedad, subasta, alquilada, proindiviso, rebaja, solo particulares, abstenerse agencias, exclusiva). El resto vale 0.
- **Rangos (paso 2):** `metros` entero 10-3100; `rooms` entero 0-20 o null; `bathrooms` entero 1-7 o null, 0 rechazado. Base: limpieza del notebook y valores mínimo y máximo de `train.csv` (metros 11-3015, habitaciones 0-20, baños 1-7).
- **Ascensor, localización y planta (paso 3):** la API acepta null y aplica la regla del preprocesado: `NO_APLICA` para casas y chalets, `DESCONOCIDO` para el resto.
- **Catálogo (paso 2):** se construye solo con `train.csv`. Las filas de test con valores fuera del catálogo (planta `22ª`) se excluyen de los fixtures.
- **Render (paso 4):** build `uv sync`, `UV_VERSION=0.12.23`, health check en `/api/v1/health`.

## Pendiente de confirmar

- Márgenes de la horquilla (`MARGEN_ERROR_GENERAL = 0.17`, `MARGEN_ERROR_LUJO = 0.24`, `UMBRAL_LUJO = 1_490_000`): se añadirán en el paso 3.
