# Registro de decisiones técnicas

Cada entrada recoge qué se decidió, por qué y qué alternativas se descartaron.
Estado: **aprobada** (confirmada por el responsable del proyecto), **informativo** o **pendiente de confirmar**.

## Índice

| Área | Decisiones |
|---|---|
| Entorno y herramientas | D-001 Python 3.14.4 · D-002 versiones fijadas · D-003 uv y `uv_build` · D-005 Ruff y pytest · D-024 httpx |
| Modelo y datos | D-006 `.gitignore` · D-007 joblib frente a pkl · D-008 reconstrucción de tags · D-009 memoria |
| Dominio | D-011 sinónimos · D-012 valores en español y etiquetas · D-013 barrio-zona · D-014 `domain/` · D-016 catálogo |
| Contrato y servicio | D-004 rutas · D-015 nombres públicos · D-018 horquilla · D-019 validación y errores · D-020 fila del modelo · D-021 redondeo · D-022 metadata · D-023 arranque y logs |
| Calidad | D-010 tests · D-017 fixtures · D-025 integración continua |
| Despliegue y documentación | D-026 Render · D-027 README |
| Fase 2: interfaz web | D-028 arquitectura y URL de la API · D-029 informe del modelo y gráficos · D-030 árbol del fondo · D-031 catálogo estático · D-032 fuentes · D-033 paleta · D-034 casas y chalets · D-035 lógica de la web · D-036 caché de la web |

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
- **Dependencias indirectas:** las que también estaban en el entorno de entrenamiento se fijan a su versión con `[tool.uv] constraint-dependencies`: contourpy 1.3.3, fonttools 4.63.0, kiwisolver 1.5.0, matplotlib 3.11.0, narwhals 2.23.0, packaging 26.2, plotly 6.9.0, pyparsing 3.3.2, scipy 1.18.0, threadpoolctl 3.6.0, tzdata 2026.2. `tzdata` solo se instala en Windows (pandas lo pide con el marcador `sys_platform == 'win32'`), así que su test se salta en Linux; no comprobarlo así hizo fallar la primera ejecución de la CI. Una restricción solo limita la versión y no instala nada por sí misma. Con ellas fijadas pasan todos los tests y `scripts/verify_model.py` carga y predice sin avisos. `tests/unit/test_entorno.py` comprueba que la versión de Python y la de cada paquete fijado son las del entrenamiento.
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
- **Tests del paso 3:** `test_horquilla.py`, `test_peticion.py` (cada campo y código), `test_predictor.py` (orden y tipos de columnas, nulos a NaN, tags a 0, reglas, redondeo, compatibilidad modelo-dominio), `test_metadata.py`, `test_errores.py`, `test_logs.py`, `integration/test_api.py` (endpoints y cada código de error por HTTP) e `integration/test_referencia.py`.
- **Tests del paso 4:** `test_despliegue.py` (coherencia de `render.yaml` y `ci.yml` con la app: health check, comando de arranque, versión de uv, comprobaciones de la CI).
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
- **Limitación aceptada:** las filas expresables son menos variadas que el conjunto completo (no hay casa rural, chalet adosado ni chalet, ni casos `DESCONOCIDO`). Esos casos se cubren con peticiones construidas a mano en `test_predictor.py` y `test_api.py`.
- **Alternativas descartadas:** filas variadas con proyección al contrato público; ambos conjuntos.

## D-018. Horquilla de precio por tramos

- **Estado:** aprobada. Implementada en `config.py` (`TRAMOS_ERROR`) y `services/horquilla.py`.
- **Qué:** el margen de la horquilla depende del tramo en que cae el precio predicho, con el error relativo de cada tramo, no con un porcentaje fijo.
- **Valores:** error relativo por tramo del modelo desplegado, redondeado (cálculo en D-029):

  | Tramo de precio predicho (€) | Error relativo |
  |---|---:|
  | menos de 250.000 | 17 % |
  | 250.000 - 435.360 | 15 % |
  | 435.360 - 835.600 | 16 % |
  | 835.600 - 1.490.000 | 15 % |
  | 1.490.000 o más | 24 % |

- **Historia:** la primera versión usaba la tabla del README de ML-idealista (16 / 15 / 16 / 15 / 24 %). En la fase 2 se comprobó que esa tabla sale de `main.ipynb`, cuyo modelo final es el pkl de 70 columnas (D-007), no el joblib desplegado. Recalculada con el joblib, solo cambia el primer tramo: 16,70 % frente a 16,42 %, que redondea a 17 %. El responsable del proyecto aprobó cambiar la API a 17 % para que la horquilla y el gráfico A coincidan. `build_model_report.py` falla si alguna vez dejan de coincidir.
- **Fuera del rango de la tabla (aprobado):** se aplica el tramo más cercano (el primero por debajo de 35.000 € y el último por encima de 13.000.000 €). Un precio exactamente en un corte pertenece al tramo superior.

## D-019. Validación en el esquema con códigos de error propios

- **Estado:** aprobada (los códigos estables vienen del contrato de `CLAUDE.md`).
- **Qué:** `schemas/prediccion.py` valida con Pydantic en modo estricto (`strict=True`: `"85"` o `85.5` no se aceptan como entero, `true` tampoco) y rechaza campos desconocidos (`extra="forbid"`). Las reglas del problema (rangos, catálogo, barrio-zona, opciones) son validadores que consultan `domain/` y lanzan `PydanticCustomError` con el código como tipo. `api/errores.py` convierte todos los errores al formato `{"errors": [{"code", "field", "message", "params"}]}` con estado 422.
- **Códigos:** `INVALID_JSON`, `FIELD_REQUIRED`, `UNKNOWN_FIELD`, `INVALID_TYPE`, `INVALID_VALUE` (genérico), `OUT_OF_RANGE` (con `min` y `max`), `BATHROOMS_ZERO`, `VALUE_NOT_IN_CATALOG`, `BARRIO_NOT_IN_ZONE` (con barrio y zona), `UNKNOWN_OPTION`, `NOT_FOUND` (404), `METHOD_NOT_ALLOWED` (405, conserva la cabecera `Allow`), `MODEL_NOT_LOADED` (503) e `INTERNAL_ERROR` (500).
- **Errores HTTP de Starlette:** un cuerpo ilegible (400, por ejemplo texto que no es UTF-8), una ruta inexistente (404) o un método no permitido (405) responderían por defecto `{"detail": ...}`. Un manejador propio los devuelve con el mismo formato y los códigos `INVALID_JSON`, `NOT_FOUND` y `METHOD_NOT_ALLOWED`. Detectado al probar el despliegue en Render; aprobado por el responsable del proyecto.
- **Orden de comprobación:** `bathrooms = 0` da `BATHROOMS_ZERO`, no `OUT_OF_RANGE`. `BARRIO_NOT_IN_ZONE` solo se evalúa si zona y barrio existen por separado; si la zona no existe, el error es `VALUE_NOT_IN_CATALOG`. Se devuelven todos los errores a la vez, no solo el primero.
- **`DESCONOCIDO` y `NO_APLICA`** no se aceptan como entrada: el usuario envía null y la API los asigna (D-014).
- **Opciones como lista de claves** (`"options": ["terrace", "renovated"]`) en lugar de 31 campos booleanos: el esquema no duplica la lista del dominio, y Swagger muestra las claves válidas como `enum`. Una clave repetida no cambia el resultado.
- **Alternativas descartadas:** validar en la ruta o en el servicio (la ruta dejaría de "solo recibir, validar y responder" a través del esquema); usar `Field(ge=..., le=...)` de Pydantic (daría sus propios códigos y `bathrooms = 0` saldría como rango).

## D-020. Construcción explícita de la fila del modelo

- **Estado:** aprobada.
- **Qué:** `services/predictor.py` asigna un valor a cada columna: los 9 campos según `domain/campos.py`, todas las columnas `flag_*`/`tag_*` a 0 de forma explícita y después a 1 las de las opciones enviadas. Si alguna columna del modelo queda sin valor, error explícito (no hay `reindex(fill_value=0)`). Tipos iguales a los de `read_csv` en el notebook: `metros` y binarias `int64`, baños y habitaciones `float64` (null pasa a NaN), categóricas `str`.
- **Comprobación al arrancar:** al crear el `Predictor` se verifica que cada columna del modelo tiene origen (campo o binaria) y que todas las columnas del dominio existen en el modelo. Un modelo incompatible impide arrancar la app, en vez de fallar en la primera petición.
- **Verificado:** las 20 filas del fixture se reconstruyen exactamente (`assert_frame_equal`) y el precio exacto del servicio es idéntico, bit a bit, a `model.predict()` sobre la fila del notebook (la API lo devuelve redondeado, D-021).

## D-021. Precios redondeados a euros enteros

- **Estado:** aprobada (sustituye a la versión inicial, que devolvía el precio sin redondear).
- **Qué:** `estimated_price`, `price_min` y `price_max` son enteros (euros). El tramo de error se elige con el precio ya redondeado, que es el que ve el usuario (un 249.999,6 se muestra como 250.000 y lleva el margen del tramo que empieza en 250.000), y los extremos se calculan sobre ese precio y se redondean. `error_margin` sigue siendo decimal (0.16).
- **Exactitud:** `Predictor.predecir_precio()` expone la salida exacta del modelo. El test de referencia comprueba que es idéntica a `model.predict()` sobre la fila del notebook y que la API devuelve exactamente ese valor redondeado.
- **Alternativa descartada:** devolver el precio sin redondear y dejar el redondeo a la interfaz. Unos céntimos sobre una estimación con un 15 % de error transmiten una precisión que no existe.

## D-022. Metadata del formulario

- **Estado:** aprobada.
- **Qué:** `GET /api/v1/metadata` devuelve campos (nombre, etiqueta es/en, obligatoriedad y rango), distritos con etiqueta y sus barrios, tipos de inmueble, ascensor, exterior/interior y plantas con etiqueta es/en (sin `DESCONOCIDO` ni `NO_APLICA`), y los dos grupos de opciones. Se construye una vez desde `domain/` y se cachea.
- **Orden:** distritos por nombre visible y barrios alfabéticos, ignorando tildes, para el desplegable con búsqueda (D-013).

## D-023. Arranque, carga del modelo y logs

- **Estado:** aprobada.
- **Qué:** `create_app()` es una fábrica (`uvicorn --factory tasador.main:create_app`); el modelo se carga una sola vez en el `lifespan` y se guarda en `app.state`. Si el archivo no existe, la app no arranca. `/api/v1/health` devuelve 200 con `model_loaded: true`, o 503 si el modelo no está cargado. `GET /` devuelve nombre, versión (de `pyproject.toml`) y enlaces.
- **HEAD:** `/` y `/api/v1/health` aceptan también `HEAD`. Render comprueba el puerto con `HEAD /` y muchos monitores de disponibilidad usan HEAD; antes respondían 405. Se registra como ruta aparte, fuera del esquema OpenAPI, porque declarar GET y HEAD en la misma ruta genera un identificador de operación duplicado en `/docs`.
- **Logs:** el logger `tasador` usa el formato de uvicorn y registra solo eventos técnicos (carga del modelo con su ruta y número de columnas, errores internos). Un test comprueba que los datos de una petición no aparecen en los logs.
- **Alternativa descartada:** variable global `app` a nivel de módulo: cargaría el modelo al importar y complicaría los tests.

## D-024. httpx para el TestClient: aviso de Starlette

- **Estado:** aprobada: se mantiene `httpx` con el aviso filtrado.
- **Qué pasa:** Starlette 1.7 emite un `DeprecationWarning` al usar el `TestClient` con `httpx` y recomienda `httpx2` (soportado desde Starlette 1.2.0, mayo de 2026). La documentación de FastAPI sigue indicando `httpx`. Como pytest convierte los avisos en errores (D-005), se ignora únicamente ese aviso en `pyproject.toml`.
- **Alternativa descartada (por ahora):** sustituirlo por `httpx2` (paquete de la organización pydantic, 2.13.1). Si una versión futura de Starlette deja de admitir `httpx`, el filtro dejará de bastar y habrá que revisarlo.
- **Fuentes:** https://github.com/Kludex/starlette/blob/main/docs/release-notes.md, https://fastapi.tiangolo.com/tutorial/testing/

## D-025. Integración continua con GitHub Actions

- **Estado:** aprobada.
- **Qué:** `.github/workflows/ci.yml` se ejecuta en cada push y pull request: `actions/checkout@v7.0.1`, `astral-sh/setup-uv@v10.2.0` con uv 0.12.23 y caché, `uv python install` (lee `.python-version`), `uv sync --locked`, `ruff format --check`, `ruff check` y `pytest`. Permisos de solo lectura.
- **Por qué:** `--locked` hace fallar la CI si `uv.lock` no corresponde a `pyproject.toml`. `ruff format --check` comprueba el formato sin modificar nada. Las acciones se fijan a versiones exactas para que un cambio de versión no altere la CI sin aviso.
- **Sin datos:** `data/` no está en el repositorio. Los 3 tests de reproducibilidad se saltan solos y el resto (incluido el de referencia, que usa los fixtures versionados) se ejecuta. Simulado en una copia limpia sin `data/` ni `.venv`: 283 pasan y 3 se saltan.
- **Alternativa descartada:** `actions/setup-python`: uv ya instala la versión de `.python-version`, como recomienda su documentación.
- **Fuentes:** https://docs.astral.sh/uv/guides/integration/github/, https://github.com/astral-sh/setup-uv

## D-026. Despliegue en Render con blueprint

- **Estado:** aprobada. El despliegue lo hace el responsable del proyecto desde el panel de Render.
- **Qué (`render.yaml`):** servicio `web`, `runtime: python`, `plan: free`, región `frankfurt`, `buildCommand: uv sync --locked --no-dev`, `startCommand: uv run --no-sync uvicorn --factory tasador.main:create_app --host 0.0.0.0 --port $PORT`, `healthCheckPath: /api/v1/health`, `autoDeployTrigger: checksPass` y `UV_VERSION=0.12.23`.
- **Por qué:**
  - Render activa uv al encontrar `uv.lock` y toma Python de `.python-version` (D-001).
  - `--no-dev` deja fuera ruff, pytest y httpx en producción.
  - `--no-sync` en el arranque evita reinstalar: el entorno ya se creó en el build.
  - `0.0.0.0` y `$PORT` son obligatorios en Render.
  - Fráncfort es la región disponible más cercana a Madrid.
  - `checksPass` solo despliega si la CI pasa.
- **Ensayado en local:** con un entorno aparte, `uv sync --locked --no-dev` no instala pytest ni ruff, y el comando de arranque levanta la app, carga el modelo y responde en health y predict.
- **Servicio creado con el formulario del panel**, no con el blueprint: `render.yaml` queda como referencia versionada de la configuración, que se introdujo a mano con los mismos valores.
- **Verificado en el primer despliegue (commit `ff69cbe`):**
  - Render instaló Python 3.14.4 desde `.python-version` y uv 0.12.23 desde `UV_VERSION`;
  - el build sin dependencias de desarrollo instaló 35 paquetes con las versiones de `uv.lock`;
  - `uv run --no-sync` funciona en tiempo de ejecución y el modelo carga (69 columnas);
  - contra la URL pública: health, raíz, metadata, `/docs`, predicción y los errores `BARRIO_NOT_IN_ZONE` y `BATHROOMS_ZERO` responden como en local, y el precio exacto en Linux es idéntico al de Windows;
  - `checksPass` funciona: el commit `8b897aa` no se desplegó porque la CI falló (ver D-002, `tzdata`).
- **Ajustes posteriores en el panel:** Health Check Path estaba vacío y se fijó a `/api/v1/health`. El primer build avisó de que Render no tenía acceso al repositorio a través de su aplicación de GitHub; sin ese acceso no recibe pushes ni el estado de la CI y `checksPass` no dispara despliegues. Se concedió el acceso y se desplegó `0944189` manualmente.
- **Verificado con `0944189` desplegado (URL pública):** precio, mínimo y máximo redondeados; tramo general (16 % y 15 %) y de lujo (24 %); chalet sin datos opcionales; `HEAD` 200 en `/` y `/api/v1/health`; `NOT_FOUND` (404), `METHOD_NOT_ALLOWED` (405 con `Allow: POST`), `INVALID_JSON` (400 con cuerpo Latin-1), varios errores 422 a la vez y `BARRIO_NOT_IN_ZONE`.
- **Memoria:** límite de 512 MB en el plan gratuito. El uso real solo se muestra en planes de pago; la referencia es la medición local (unos 192 MiB, D-009).
- **Alternativas descartadas:** `pip install` con un `requirements.txt` exportado (duplicaría `uv.lock`); `autoDeployTrigger: commit` (podría desplegar un commit con tests rotos).
- **Fuentes:** https://render.com/docs/blueprint-spec, https://render.com/docs/uv-version, https://render.com/docs/troubleshooting-python-deploys, https://render.com/docs/web-services, https://render.com/docs/health-checks, https://render.com/docs/free

## D-027. README

- **Estado:** aprobada.
- **Qué:** en español. Incluye qué es, el origen del modelo, las métricas en test indicadas por el responsable (MAE 180.710 €, RMSE 439.765 €, R² 0,863), la tabla de tramos, cómo ejecutarlo en local con uv, los endpoints con ejemplos reales, la tabla de códigos de error, el despliegue y el arranque en frío de Render (15 minutos sin tráfico, alrededor de un minuto para despertar), las limitaciones y la autoría (Ramiro Caruso y Ana Manzanares, con el EDA acreditado a Ana).
- **Fecha de los datos:** anuncios de Idealista Madrid de 2025, confirmado por el responsable del proyecto. El README lo indica en el origen del modelo y en las limitaciones.

## D-028. Arquitectura de la interfaz web y URL de la API

- **Estado:** aprobada en el paso 0 de la fase 2. Implementada en el paso 2.
- **Qué:** archivos estáticos puros en `src/tasador/web/` (HTML, CSS y JavaScript sin build, sin frameworks ni plantillas). En local los sirve la propia app FastAPI en `/`; en producción se publican además como Static Site de Render.
- **`GET /`:** pasa a servir la web. La información JSON de la fase 1 (nombre, versión, enlaces) se mueve a `GET /api/v1/` y `HEAD /` sigue respondiendo 200. Es un cambio de contrato aprobado expresamente.
- **La API sirve la web siempre**, también en el Web Service de producción: un solo camino de código. Los usuarios entran por el Static Site.
- **Cómo se sirve (`api/raiz.py`):** `index.html` en `/` y cada carpeta de `web/` montada en su ruta (`/css`, `/js`, `/datos`, `/i18n`) más una ruta por archivo de la raíz (`/config.js`). No se monta un `StaticFiles` sobre `/` porque capturaría las rutas de la API: un `DELETE /api/v1/predict` caería en los archivos estáticos y daría un 405 sin la cabecera `Allow` correcta. La web se registra después de la API.
- **URL base de la API:** `web/config.js` versionado con `window.TASADOR_CONFIG = { apiBaseUrl: "", portfolioUrl: "" }` (cadena vacía = mismo origen). En el Static Site, el comando de build sobrescribe ese archivo con las variables `API_BASE_URL` y `PORTFOLIO_URL` del panel, de modo que la URL cambia sin tocar el código y el enlace al portfolio queda oculto mientras esté vacío.
- **CORS:** `CORSMiddleware` de Starlette (sin dependencias nuevas) con los orígenes de la variable `ALLOWED_ORIGINS`, separados por comas (se ignoran espacios y la barra final). Solo `GET` y `POST` y la cabecera `Content-Type`. Sin la variable no se admite ningún origen ajeno. `create_app(origenes_permitidos=...)` permite fijarlos en los tests. Limitación conocida: las respuestas 500 las genera el middleware más externo de Starlette, sin cabeceras CORS; el navegador las verá como error de red, y la web muestra el mismo mensaje.
- **Verificado en Render:** la documentación no dice de forma explícita que las variables de entorno estén disponibles en el build de un Static Site, así que se comprobó en el primer despliegue (https://ml-vivienda-madrid-1.onrender.com): el `config.js` publicado contiene `apiBaseUrl: "https://ml-vivienda-madrid.onrender.com"`, tomado de `API_BASE_URL`.
- **URLs de producción:** API (Web Service) https://ml-vivienda-madrid.onrender.com; web (Static Site) https://ml-vivienda-madrid-1.onrender.com. El sufijo `-1` lo añadió Render porque el nombre ya estaba en uso.
- **Alternativa descartada:** reescritura `/api/*` del Static Site hacia la API (evitaría CORS). La documentación no aclara los tiempos de espera ni el soporte de POST, y la API tarda unos 50 s en despertar.
- **Fuentes:** https://render.com/docs/static-sites, https://render.com/docs/blueprint-spec, https://render.com/docs/deploy-create-react-app, https://render.com/docs/redirects-rewrites

## D-029. Informe del modelo para los gráficos

- **Estado:** aprobada.
- **Qué:** `scripts/build_model_report.py` carga el joblib, predice sobre `data/test.csv` (excepción de este proyecto a la regla de no evaluar) y escribe `web/datos/informe_modelo.json`. Es determinista (misma huella en dos ejecuciones) y un test local compara el archivo versionado con el generado.
- **Métricas verificadas:** joblib MAE 180.709,77 €, RMSE 439.764,62 €, R² 0,8635 (el informe guarda 0,863476: con solo cuatro decimales la web redondeaba dos veces y mostraba 0,864 en lugar de 0,863), idénticas a la salida guardada de `modeling.ipynb` (celda 36). Las de `main.ipynb` (MAE 181.256,21 €) corresponden al pkl de 70 columnas: `main.ipynb` calcula los tags con el dataset completo antes de separar train y test, y por eso aparece `tag_seguridad`. El script falla si las métricas no coinciden con las documentadas.
- **Error relativo (gráfico A):** no está calculado en ningún notebook. `main.ipynb` (celda 96) calcula, por quintil de precio real (`pd.qcut(y_test, q=5)`), el precio mediano y el MAE; el porcentaje del README es MAE del tramo / precio mediano del tramo. Con el joblib: 16,70 %, 14,78 %, 15,53 %, 15,48 % y 23,60 %. Los cortes son los de la horquilla de la API, y el script comprueba que los porcentajes redondeados coinciden con `TRAMOS_ERROR`.
- **Gráfico B:** los 2.237 pares real/predicho de test en euros enteros, ordenados por precio real.
- **Gráfico C:** `get_feature_importance()` del CatBoost final (metros 41,675 %, zona 23,129 %, barrio 7,852 %, como en `modeling.ipynb`, celda 38). Los 9 campos principales llevan su etiqueta es/en del dominio; las binarias se muestran con el nombre de la columna. La web muestra las 10 variables más importantes y agrupa el resto en una sola barra «otras variables…» / «other features…» (aprobado).
- **Gráfico D:** no se recalcula (requeriría reentrenar). Serie de `modeling.ipynb`, la historia del modelo desplegado, con los valores de sus salidas guardadas: regresión lineal 356.861 €, XGBoost 220.516 €, LightGBM 223.028 €, CatBoost 201.014 €, CatBoost con log del precio 190.149 €, + Optuna 185.803 €, + tags 178.584 € (validación cruzada de 5 folds) y modelo final 180.710 € (test). Cada punto guarda su celda de origen y su conjunto (`cv` o `test`), que la web marcará distinto.
- **Alternativa descartada:** la comparativa de `main.ipynb`. Le falta la salida del CatBoost sin optimizar y termina en el otro modelo.

## D-030. Árbol del fondo animado

- **Estado:** aprobada (árbol 0).
- **Qué:** `scripts/export_tree.py` escribe `web/datos/arbol.json` con los 9 cortes del árbol 0 y el recorrido de las 20 viviendas de los fixtures. No necesita `data/`, así que su determinismo y su vigencia se comprueban también en la CI.
- **Funciones de CatBoost:** `CatBoostRegressor.plot_tree(tree_idx, pool)` para la descripción de cada corte (solo se usa el texto del `graphviz.Digraph`; no hace falta el programa Graphviz) y `calc_leaf_indexes(pool, ntree_start, ntree_end)` para la hoja de cada vivienda.
- **Orden de niveles y bits:** el de `plot_tree`, de la raíz hacia abajo. El nivel L corresponde al bit (profundidad - 1 - L) del índice de hoja y la rama "Yes" al 1. Verificado con las 2.237 filas de test en los cinco niveles numéricos o binarios (coincidencia del 100 %), y comprobado de nuevo en cada ejecución del script, que falla si no se cumple. La exportación JSON del modelo lista los cortes en el orden contrario; en un árbol simétrico ambos órdenes dan las mismas 512 hojas.
- **Cortes categóricos:** CatBoost no compara la categoría sino un estadístico del precio por categoría (CTR) discretizado. Se muestran como `ctr(zona) > 3`, sin inventar condiciones del tipo `zona = centro`.
- **Por qué el árbol 0:** es el primero que aprendió el modelo, fácil de justificar. Alternativa descartada: elegir el más legible entre los primeros 50.
- **Fuentes:** https://catboost.ai/docs/en/concepts/python-reference_catboostregressor_plot_tree, https://catboost.ai/docs/en/concepts/python-reference_catboost_calc_leaf_indexes, https://github.com/catboost/tutorials/blob/master/model_analysis/model_export_as_json_tutorial.ipynb

## D-031. Catálogo estático para el formulario

- **Estado:** aprobada.
- **Qué:** `scripts/build_web_catalog.py` guarda en `web/datos/catalogo.json` exactamente la respuesta de `GET /api/v1/metadata`. Un test lo compara con la respuesta real de la API, y otro con lo que genera el dominio.
- **Por qué:** el formulario funciona al instante aunque la API esté dormida.

## D-032. Fuentes

- **Estado:** aprobada. Se alojan en el proyecto en el paso 3, con sus licencias.
- **Qué:** IBM VGA 9x16 en su variante "Plus" (Ultimate Oldschool PC Font Pack 2.2, de VileR) para títulos, marca y bordes; IBM Plex Mono para el resto.
- **Licencias:** Oldschool PC Font Pack, CC BY-SA 4.0: exige atribución ("VileR", con enlace a https://int10h.org/oldschool-pc-fonts/), que irá en el pie. IBM Plex Mono, SIL OFL 1.1.
- **Cobertura comprobada:** IBM VGA 9x16 Plus tiene tildes, ñ, ª, € y caracteres de caja. La variante "437" no tiene ÁÍÓÚ ni €.
- **Alternativa descartada:** VT323 (OFL 1.1), sin caracteres de caja.
- **Incertidumbre:** se entiende que la cláusula ShareAlike solo afecta a modificaciones de la fuente, no a la web que la usa. No es asesoramiento legal.

## D-033. Paleta

- **Estado:** aprobada (opción A, P1 clásico).
- **Qué:** fondo `#060a06`, verde principal `#33ff66`, verde atenuado `#1f9d45`, verde tenue `#0f3d1c`. Contraste WCAG sobre el fondo: principal 14,8; atenuado 5,7 (válido para texto secundario); tenue 1,6, solo decorativo (árbol y rejilla).
- **Errores:** vídeo inverso (texto en color de fondo sobre bloque verde principal) con prefijo `ERROR:`. **Foco:** contorno de 2 px en verde principal y vídeo inverso en los botones.

## D-034. Casas y chalets en el formulario

- **Estado:** aprobada.
- **Verificado:** en `data/train.csv`, las 543 filas de los cinco tipos de casa o chalet tienen planta, ascensor y localización siempre a `NO_APLICA`.
- **Qué:** si el tipo es de casa o chalet, el formulario oculta esos tres campos y los envía como `null`. La web sabe qué tipos son casa o chalet por el campo `is_house` de cada tipo en `GET /api/v1/metadata`, calculado desde `TIPOS_CASA_O_CHALET` del dominio: cambio aditivo del contrato, aprobado, que evita duplicar la regla en el JavaScript. La API no acepta `"NO_APLICA"` como entrada (D-019) pero convierte `null` en `NO_APLICA` para esos tipos (D-014), así que el modelo recibe exactamente lo mismo sin cambiar el contrato.

## D-035. Lógica de la interfaz web

- **Estado:** aprobada (requisitos de la fase 2). Implementada en el paso 2; la estética llega en el paso 3.
- **Estructura:** `index.html` semántico con módulos ES sin build (`js/app.js` como entrada; `i18n.js`, `api.js`, `arranque.js`, `combobox.js`, `formulario.js`, `resultado.js`, `formato.js`). Sin frameworks ni dependencias.
- **Idiomas:** `i18n/es.json` e `i18n/en.json` con las mismas claves (comprobado por test). Los elementos con `data-i18n` reciben su texto; las etiquetas de campos, tipos, plantas, grupos y opciones salen del catálogo (bilingüe desde el dominio). Idioma inicial: el guardado en `localStorage` o, si no hay, el del navegador; cambia también `lang` del documento. Zonas y barrios no se traducen.
- **Registro de arranque:** al cargar se llama a `/api/v1/health` sin esperar al formulario. Si no responde en 2,5 s, el registro avisa de que la instancia despierta y añade una línea cada 15 s; reintenta cada 3 s hasta 150 s. Los envíos hechos antes de que la API esté lista esperan en cola y el registro lo indica. La barra de estado muestra `api`, `modelo` (versión del informe) e `idioma`.
- **Formulario:** distrito y barrio son desplegables con búsqueda (patrón combobox de ARIA, filtro sin tildes ni mayúsculas, flechas, Intro y Escape); el barrio solo ofrece los del distrito elegido. Habitaciones y baños tienen "no lo sé" (se envían `null`). "Más opciones" es un `details` cerrado con las 31 casillas en dos `fieldset`.
- **Validación en el cliente:** mismas reglas y mismos códigos que la API (`FIELD_REQUIRED`, `INVALID_TYPE`, `OUT_OF_RANGE` con los rangos del catálogo, `BATHROOMS_ZERO`). Los errores de la API llegan con sus códigos estables y se muestran junto a su campo con el prefijo `ERROR:`; los que no tienen campo, en un resumen. Dos códigos son solo de la web: `RED` y `DESCONOCIDO`.
- **Resultado:** precio redondeado a miles con formato por idioma (`1.102.000 €` / `€1,102,000`), margen y horquilla tal como los devuelve la API, anunciado con `aria-live`.
- **Verificado en Chrome (local):** desplegable encadenado, caso chalet, "más opciones", errores de validación, predicción completa, cambio de idioma y registro de arranque sin API (sirviendo solo los estáticos).

## D-036. Caché de los archivos de la web

- **Estado:** aprobada como corrección técnica del paso 2.
- **Problema detectado:** al regenerar `informe_modelo.json` y cambiar `app.js`, el navegador siguió usando las versiones anteriores de su caché, incluso al recargar. En producción, cada despliegue podría servir JavaScript y datos atrasados.
- **Qué:** la app sirve todos los archivos de la web con `Cache-Control: no-cache`: el navegador puede guardarlos, pero los revalida con el servidor (ETag) en cada carga y solo los vuelve a descargar si han cambiado. Las respuestas de la API no llevan esa cabecera.
- **Pendiente (paso 4):** la misma cabecera en el Static Site de Render (regla `/*` en `render.yaml` y en el panel).
- **Alternativas descartadas:** `fetch(..., { cache: "no-cache" })` en el JavaScript (no cubre los propios módulos JS ni el CSS); nombres de archivo con huella (`app.3f2a.js`), que exigirían un paso de build.

---

## Pendiente de confirmar

- `ALLOWED_ORIGINS` en el Web Service de Render (`https://ml-vivienda-madrid-1.onrender.com`) para que el Static Site pueda llamar a la API (D-028).
- Cabecera `Cache-Control: no-cache` en el Static Site (D-036, paso 4).
