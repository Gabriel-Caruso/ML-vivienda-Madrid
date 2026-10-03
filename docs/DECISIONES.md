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
- **Dependencias indirectas:** las que también estaban en el entorno de entrenamiento se fijan a su versión con `[tool.uv] constraint-dependencies`: contourpy 1.3.3, fonttools 4.63.0, kiwisolver 1.5.0, matplotlib 3.11.0, narwhals 2.23.0, packaging 26.2, plotly 6.9.0, pyparsing 3.3.2, scipy 1.18.0, threadpoolctl 3.6.0, tzdata 2026.2. Una restricción solo limita la versión y no instala nada por sí misma. Con ellas fijadas pasan todos los tests y `scripts/verify_model.py` carga y predice sin avisos. `tests/unit/test_entorno.py` comprueba que la versión de Python y la de cada paquete fijado son las del entrenamiento.
- **Alternativas descartadas:** dejar las indirectas libres (primera versión de esta decisión): no forman parte del objeto serializado, pero fijarlas elimina una fuente de diferencias sin coste. Declararlas como dependencias directas: daría a entender que el código las usa.
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
- **Reglas desactivadas:** `SIM110` (pide cambiar bucles `for` por `any()`/`all()` con generador; el estilo del proyecto prefiere bucles explícitos) y `SIM300` (toma las constantes del dominio en mayúsculas, como `RANGO_METROS`, por literales y pide escribir la comparación al revés).
- **pytest `pythonpath = ["scripts"]`:** permite testear las funciones puras de los scripts sin convertirlos en paquete.
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

## D-010. Tests de todo lo programado, en cada paso

- **Estado:** aprobada.
- **Qué:** cada vez que se termina de programar algo se añaden sus tests y se ejecuta la batería completa (Ruff + pytest). Ningún paso se da por terminado sin ello.
- **Tests del paso 1:** `test_config.py` (rutas), `test_entorno.py` (versiones del entrenamiento) y `test_modelo.py` (carga sin avisos, tipo y transformación del objetivo, 69 columnas por grupo y posición, categóricas nativas, predicción finita sobre una fila construida a mano). Fixtures de sesión en `tests/conftest.py` cargan el modelo, el catálogo y las filas de referencia una sola vez.
- **Tests del paso 2:** `test_reglas.py`, `test_rangos.py`, `test_etiquetas.py`, `test_catalogo.py`, `test_tags.py`, `test_campos.py`, `test_fixtures.py`, `test_scripts.py` (funciones puras de los scripts con datos sintéticos) e `integration/test_reproducibilidad.py`.
- **Por qué no se usan los CSV en los tests:** `data/` no está en el repositorio, así que en la CI no existiría. Los tests usan solo lo versionado (modelo, catálogo y fixtures). La única excepción es `test_reproducibilidad.py`, que se salta automáticamente si no hay CSV: en local comprueba que el catálogo y los fixtures versionados son exactamente los que generan los scripts.

## D-011. Pares de tags sinónimos: una sola casilla

- **Estado:** aprobada.
- **Qué:** "Reformado" activa `tag_reformado` y `tag_reformada`; "A estrenar / nuevo" activa `tag_estrenar` y `tag_nuevo`. Cada par es una sola casilla en el contrato público.
- **Por qué:** para el usuario son la misma característica; dos casillas obligarían a elegir entre sinónimos sin criterio. Marcar ambas columnas reproduce el caso de un anuncio que usa las dos palabras.
- **Alternativa descartada:** dos casillas por par.

## D-012. Valores de las categóricas en español; etiquetas legibles y bilingües

- **Estado:** aprobada.
- **Qué:** los valores de las categóricas del contrato (tipo de inmueble, zona, barrio, planta...) se envían en español, igual que en el modelo. Los nombres de campo siguen en inglés (`bathrooms`, `district`...). Para mostrar, cada campo, valor y tag tendrá una etiqueta legible en español y en inglés ("Baños" / "Bathrooms", no `baños_limpio`), definida en `domain/` y servida por `/api/v1/metadata`, para que la interfaz de la fase 2 no tenga que traducir nombres internos.
- **Por qué:** los valores en español evitan una segunda tabla de mapeo entre el contrato y el modelo. Las etiquetas en el dominio mantienen todo el conocimiento del problema en un solo sitio.
- **Alternativa descartada:** códigos en inglés para los valores (`flat`, `penthouse`): duplicaría el catálogo y añadiría un mapeo más sin beneficio para el usuario, que verá siempre la etiqueta traducida.

## D-013. Relación barrio-zona: se respeta la jerarquía de los datos, verificada

- **Estado:** aprobada (la API no debe aceptar un barrio de otra zona).
- **Qué hay en los datos:** `train.csv` solo contiene Madrid capital (`provincia = madrid`): 21 zonas (los 21 distritos municipales) y 139 barrios, cada uno en una única zona. No hay barrios de otros municipios (por ejemplo, San Sebastián de los Reyes).
- **Origen de la jerarquía:** es la de Idealista. Sus URLs siguen el patrón `/venta-viviendas/madrid/<zona>/<barrio>/` con los mismos identificadores de zona que los datos (`centro`, `chamartin`, `barrio-de-salamanca`...).
- **Verificación:** se contrastaron los 139 barrios con la lista oficial de barrios administrativos por distrito. Los barrios de Idealista agrupan o subdividen los oficiales (`Chueca-Justicia` = Justicia, `Palos de la Frontera` = Palos de Moguer, `Sanchinarro` y `Valdebebas - Valdefuentes` dentro de Valdefuentes, `Las Tablas` y `Montecarmelo` en Fuencarral-El Pardo, `Los Ahijones`, `Los Berrocales` y `Los Cerros` en Vicálvaro, `Valdecarros` en Villa de Vallecas). En ningún caso aparece un barrio asignado a un distrito que no le corresponda.
- **Cómo se aplica:** el catálogo (paso 2) guarda cada zona con su lista de barrios; `/api/v1/metadata` los sirve agrupados para que el formulario solo ofrezca los barrios de la zona elegida; la API rechaza con `BARRIO_NOT_IN_ZONE` cualquier combinación que no esté en el catálogo (paso 3), con tests de ambos lados.
- **Alternativa descartada:** reasignar barrios a distritos según la lista oficial. El modelo aprendió con la asignación de los datos; cambiarla le daría combinaciones zona-barrio que nunca vio. Además la verificación no encontró nada que corregir.
- **Nombres visibles:** zonas y barrios no se traducen. Los identificadores de zona (`fuencarral`, `san-blas`...) se mostrarán con el nombre oficial del distrito, igual en español y en inglés (aprobado; implementado en `domain/etiquetas.py`):

  | Valor en los datos | Nombre visible |
  |---|---|
  | arganzuela | Arganzuela |
  | barajas | Barajas |
  | barrio-de-salamanca | Salamanca |
  | carabanchel | Carabanchel |
  | centro | Centro |
  | chamartin | Chamartín |
  | chamberi | Chamberí |
  | ciudad-lineal | Ciudad Lineal |
  | fuencarral | Fuencarral-El Pardo |
  | hortaleza | Hortaleza |
  | latina | Latina |
  | moncloa | Moncloa-Aravaca |
  | moratalaz | Moratalaz |
  | puente-de-vallecas | Puente de Vallecas |
  | retiro | Retiro |
  | san-blas | San Blas-Canillejas |
  | tetuan | Tetuán |
  | usera | Usera |
  | vicalvaro | Vicálvaro |
  | villa-de-vallecas | Villa de Vallecas |
  | villaverde | Villaverde |

  Los barrios ya vienen con su nombre legible y se muestran tal cual.
- **Fuentes:** https://www.madrid.es/portales/munimadrid/es/SER/Distritos-y-barrios/?vgnextfmt=default&vgnextoid=5a86befb3fd31810VgnVCM2000001f4a900aRCRD&vgnextchannel=4947b5793cba4410VgnVCM2000000c205a0aRCRD, https://en.wikipedia.org/wiki/List_of_neighborhoods_of_Madrid, https://www.idealista.com/en/venta-viviendas/madrid/centro/

- **Selección en el formulario (fase 2):** distrito y barrio serán desplegables en los que se puede escribir para filtrar (combobox con búsqueda). Para facilitarlo, el catálogo ordena zonas y barrios ignorando tildes y mayúsculas ("Águilas" junto a "Aluche", no al final), y `/api/v1/metadata` entregará los barrios agrupados por zona.

## D-014. Organización de `domain/`

- **Estado:** aprobada.
- **Qué:** un módulo por tipo de conocimiento, todos sin dependencias de pandas ni del modelo:
  - `reglas.py`: reglas del preprocesado (`NO_APLICA` para los 5 tipos de casa o chalet y `DESCONOCIDO` para el resto cuando falta ascensor, localización o planta; un estudio sin habitaciones tiene 0).
  - `rangos.py`: rangos aprobados (`metros` 10-3100, habitaciones 0-20, baños 1-7).
  - `etiquetas.py`: textos visibles en español e inglés (nombres de distrito, tipos de inmueble, ascensor, exterior/interior, plantas).
  - `tags.py`: las 31 casillas (22 de vivienda y 9 legales) que activan 33 columnas binarias del modelo.
  - `campos.py`: los 9 campos principales del contrato y su columna del modelo, en el orden del modelo.
  - `catalogo.py` + `catalogo.json`: valores categóricos válidos y relación zona-barrio.
- **Por qué:** el conocimiento del problema queda en un solo sitio y se puede testear sin levantar la API. `campos.py` y `tags.py` son el único lugar donde se relaciona el contrato público con las columnas del modelo.
- **Etiquetas de planta:** se generan por regla ("3ª" -> "3ª planta" / "3rd floor"; "-1" -> "Sótano (-1)" / "Basement (-1)", porque en el preprocesado "SÓTANO" pasó a "-1"). Un formato no reconocido lanza un error en vez de mostrar un texto inventado.

## D-015. Nombres públicos de los campos

- **Estado:** aprobada.
- **Qué:** `area_m2` (metros), `bathrooms`, `rooms`, `district` (zona), `neighbourhood` (barrio), `property_type`, `lift` (ascensor), `position` (exterior/interior), `floor` (planta). Casillas: `terrace`, `garage`, `renovated`, `squatted`... (lista completa en `domain/tags.py`).
- **Por qué:** inglés, snake_case y sin caracteres especiales, como pide el contrato. `position` evita `orientation`, que en inmobiliaria sugiere norte/sur.

## D-016. Catálogo generado y versionado dentro del paquete

- **Estado:** aprobada.
- **Qué:** `scripts/build_catalog.py` lee `data/train.csv` y escribe `src/tasador/domain/catalogo.json` con: versión del formato, hash SHA-256 del CSV de origen, zonas con sus barrios, tipos de inmueble, valores de ascensor, localización y plantas. Incluye `DESCONOCIDO` y `NO_APLICA`, que son valores que vio el modelo.
- **Reproducible:** listas ordenadas con reglas deterministas (alfabético sin tildes; plantas de abajo arriba), sin fechas, saltos de línea LF. Dos ejecuciones producen el mismo archivo byte a byte (comprobado por hash), y un test de integración compara el archivo versionado con el generado.
- **Comprobación de integridad:** el script falla si un barrio aparece en más de una zona.
- **Alternativas descartadas:** generar el catálogo al arrancar la API (obligaría a desplegar los CSV); guardarlo como módulo Python (mezcla datos generados con código escrito a mano).

## D-017. Fixtures: solo filas que la API puede expresar

- **Estado:** aprobada.
- **Qué:** `scripts/build_fixtures.py` reconstruye `data/test.csv` como el notebook y se queda con las filas "expresables": ninguna columna binaria activa fuera de las 33 públicas, pares de sinónimos coherentes y todos los valores categóricos en el catálogo. Son 50 de 2.237. De ellas elige 20 con `random_state=42`, priorizando primero todos los tipos de inmueble, después todas las filas con baños y después zonas no cubiertas. Guarda solo las 69 columnas del modelo, en su orden, y el índice de la fila en test para trazabilidad.
- **Resultado:** 15 zonas, 6 tipos de inmueble, 5 filas con baños y 15 sin ellos, estudios con 0 habitaciones, casas y chalets con `NO_APLICA`, filas sin tags y con varios tags y flags legales.
- **Por qué:** el test de referencia (paso 3) compara la respuesta de la API con `model.predict()` sobre la fila exacta del notebook, sin ninguna proyección intermedia que el test diera por buena.
- **Limitación aceptada:** las filas expresables son menos variadas que el conjunto completo (no hay casa rural, chalet adosado ni chalet, ni casos `DESCONOCIDO`). Los tests unitarios del paso 3 cubrirán esos casos con peticiones construidas a mano.
- **Alternativas descartadas:** filas variadas con proyección al contrato público; ambos conjuntos.

## D-018. Horquilla de precio por tramos

- **Estado:** aprobada la regla; valores provisionales hasta recalcularlos con el joblib. Implementada en `config.py` (`TRAMOS_ERROR`) y `services/horquilla.py`.
- **Qué:** el margen de la horquilla depende del tramo en que cae el precio predicho, con el error relativo de cada tramo, no con un porcentaje fijo.
- **Valores provisionales (README de ML-idealista):**

  | Tramo de precio predicho (€) | Error relativo |
  |---|---:|
  | menos de 250.000 | 16 % |
  | 250.000 - 435.360 | 15 % |
  | 435.360 - 835.600 | 16 % |
  | 835.600 - 1.490.000 | 15 % |
  | 1.490.000 o más | 24 % |

- **Duda abierta:** las métricas globales de ese README (MAE 181.256 €, RMSE 443.717 €, R² 0,861) no coinciden con las del modelo joblib que se despliega (MAE 180.710 €, RMSE 439.765 €, R² 0,863). Probablemente la tabla se calculó con el modelo antiguo (el pkl, D-007). El responsable del proyecto recalculará los tramos con el joblib; hasta entonces se usan estos valores como provisionales.
- **Fuera del rango de la tabla (aprobado):** se aplica el tramo más cercano (el primero por debajo de 35.000 € y el último por encima de 13.000.000 €). Un precio exactamente en un corte pertenece al tramo superior.

## D-019. Validación en el esquema con códigos de error propios

- **Estado:** aprobada (los códigos estables vienen del contrato de `CLAUDE.md`).
- **Qué:** `schemas/prediccion.py` valida con Pydantic en modo estricto (`strict=True`: `"85"` o `85.5` no se aceptan como entero, `true` tampoco) y rechaza campos desconocidos (`extra="forbid"`). Las reglas del problema (rangos, catálogo, barrio-zona, opciones) son validadores que consultan `domain/` y lanzan `PydanticCustomError` con el código como tipo. `api/errores.py` convierte todos los errores al formato `{"errors": [{"code", "field", "message", "params"}]}` con estado 422.
- **Códigos:** `INVALID_JSON`, `FIELD_REQUIRED`, `UNKNOWN_FIELD`, `INVALID_TYPE`, `INVALID_VALUE` (genérico), `OUT_OF_RANGE` (con `min` y `max`), `BATHROOMS_ZERO`, `VALUE_NOT_IN_CATALOG`, `BARRIO_NOT_IN_ZONE` (con barrio y zona), `UNKNOWN_OPTION`, `MODEL_NOT_LOADED` (503) e `INTERNAL_ERROR` (500).
- **Orden de comprobación:** `bathrooms = 0` da `BATHROOMS_ZERO`, no `OUT_OF_RANGE`. `BARRIO_NOT_IN_ZONE` solo se evalúa si zona y barrio existen por separado; si la zona no existe, el error es `VALUE_NOT_IN_CATALOG`. Se devuelven todos los errores a la vez, no solo el primero.
- **`DESCONOCIDO` y `NO_APLICA`** no se aceptan como entrada: el usuario envía null y la API los asigna (D-014).
- **Opciones como lista de claves** (`"options": ["terrace", "renovated"]`) en lugar de 31 campos booleanos: el esquema no duplica la lista del dominio, y Swagger muestra las claves válidas como `enum`. Una clave repetida no cambia el resultado.
- **Alternativas descartadas:** validar en la ruta o en el servicio (la ruta dejaría de "solo recibir, validar y responder" a través del esquema); usar `Field(ge=..., le=...)` de Pydantic (daría sus propios códigos y `bathrooms = 0` saldría como rango).

## D-020. Construcción explícita de la fila del modelo

- **Estado:** aprobada.
- **Qué:** `services/predictor.py` asigna un valor a cada columna: los 9 campos según `domain/campos.py`, todas las columnas `flag_*`/`tag_*` a 0 de forma explícita y después a 1 las de las opciones enviadas. Si alguna columna del modelo queda sin valor, error explícito (no hay `reindex(fill_value=0)`). Tipos iguales a los de `read_csv` en el notebook: `metros` y binarias `int64`, baños y habitaciones `float64` (null pasa a NaN), categóricas `str`.
- **Comprobación al arrancar:** al crear el `Predictor` se verifica que cada columna del modelo tiene origen (campo o binaria) y que todas las columnas del dominio existen en el modelo. Un modelo incompatible impide arrancar la app, en vez de fallar en la primera petición.
- **Verificado:** las 20 filas del fixture se reconstruyen exactamente (`assert_frame_equal`) y la predicción de la API es idéntica, bit a bit, a `model.predict()` sobre la fila del notebook.

## D-021. Respuesta de predicción sin redondear

- **Estado:** aprobada.
- **Qué:** `estimated_price`, `error_margin`, `price_min` y `price_max` como números sin redondear (euros).
- **Por qué:** el redondeo es cosa de presentación (la interfaz formateará según el idioma) y permite que el test de referencia exija igualdad exacta con `model.predict()`.

## D-022. Metadata del formulario

- **Estado:** aprobada.
- **Qué:** `GET /api/v1/metadata` devuelve campos (nombre, etiqueta es/en, obligatoriedad y rango), distritos con etiqueta y sus barrios, tipos de inmueble, ascensor, exterior/interior y plantas con etiqueta es/en (sin `DESCONOCIDO` ni `NO_APLICA`), y los dos grupos de opciones. Se construye una vez desde `domain/` y se cachea.
- **Orden:** distritos por nombre visible y barrios alfabéticos, ignorando tildes, para el desplegable con búsqueda (D-013).

## D-023. Arranque, carga del modelo y logs

- **Estado:** aprobada.
- **Qué:** `create_app()` es una fábrica (`uvicorn --factory tasador.main:create_app`); el modelo se carga una sola vez en el `lifespan` y se guarda en `app.state`. Si el archivo no existe, la app no arranca. `/api/v1/health` devuelve 200 con `model_loaded: true`, o 503 si el modelo no está cargado. `GET /` devuelve nombre, versión (de `pyproject.toml`) y enlaces.
- **Logs:** el logger `tasador` usa el formato de uvicorn y registra solo eventos técnicos (carga del modelo con su ruta y número de columnas, errores internos). Un test comprueba que los datos de una petición no aparecen en los logs.
- **Alternativa descartada:** variable global `app` a nivel de módulo: cargaría el modelo al importar y complicaría los tests.

## D-024. httpx para el TestClient: aviso de Starlette

- **Estado:** pendiente de decidir.
- **Qué pasa:** Starlette 1.7 emite un `DeprecationWarning` al usar el `TestClient` con `httpx` y recomienda `httpx2` (soportado desde Starlette 1.2.0, mayo de 2026). La documentación de FastAPI sigue indicando `httpx`. Como pytest convierte los avisos en errores (D-005), se ignora únicamente ese aviso en `pyproject.toml`.
- **Opciones:** mantener `httpx` con el aviso filtrado (actual), o sustituirlo por `httpx2` (paquete de la organización pydantic, 2.13.1) y quitar el filtro.
- **Fuentes:** https://github.com/Kludex/starlette/blob/main/docs/release-notes.md, https://fastapi.tiangolo.com/tutorial/testing/

---

## Decisiones aprobadas para pasos siguientes

- **Render (paso 4):** build `uv sync`, `UV_VERSION=0.12.23`, health check en `/api/v1/health`, arranque `uvicorn --factory tasador.main:create_app --host 0.0.0.0 --port $PORT`.

## Pendiente de confirmar

- Tramos de la horquilla calculados con el modelo joblib (D-018).
- `httpx` o `httpx2` para el TestClient (D-024).
