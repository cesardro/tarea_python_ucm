# Multas de circulación de Madrid

Trabajo final de **Tarea python para desarrolladores** (Máster Big Data & Data Engineering, UCM).

Paquete de Python que descarga, guarda en una caché local, limpia y analiza los datos mensuales de
multas de circulación del [portal de datos abiertos del Ayuntamiento de Madrid](https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/downloads)
(datos desde junio de 2017).

- **Autor:** Cesar Alejandro Solano Suarez
- **Entrega límite:** 15/10/2026

---

## Índice

1. [Instalación](#1-instalación)
2. [Uso](#2-uso)
3. [Descripción del paquete](#3-descripción-del-paquete)
4. [Tests](#4-tests)
5. [Declaración responsable y uso de IA](#5-declaración-responsable-sobre-autoría-y-uso-ético-de-inteligencia-artificial)

---

## 1. Instalación

### Desde el wheel (otro proyecto)

```bash
# Con uv, dentro del proyecto donde se quiere usar
uv add ruta/ejemplo_paquete/dist/tarea_python_ucm-0.1.0-py3-none-any.whl

# o, si ya estaba instalado y se quiere reinstalar
uv pip install ruta/ejemplo_paquete/dist/tarea_python_ucm-0.1.0-py3-none-any.whl --reinstall

# Sin uv
pip install ruta/ejemplo_paquete/dist/tarea_python_ucm-0.1.0-py3-none-any.whl
```

### Desde el código fuente (para desarrollar o ejecutar los tests)

```bash
cd tarea_python_ucm
uv sync            # crea .venv e instala el paquete con sus dependencias y las de desarrollo
```

---

## 2. Uso

### Ejemplo

```python
from tarea_python_ucm import MadridFines, MadridError

multas = MadridFines("multas", 7)     # caché en ~/.my_cache/multas, válida 7 días

multas.add(2024, 12)                  # añade diciembre de 2024
multas.add(2019, 5)                   # añade mayo de 2019
print(multas.loaded)                  # [(12, 2024), (5, 2019)]

print(multas.fines_calification())    # multas por tipo, mes y año
print(multas.total_payment())         # importe máximo y mínimo por mes y año
multas.fines_hour("evolucion_multas.png")   # gráfico de multas por hora

try:
    multas.add(2016, 1)
except MadridError as e:
    print(e)                          # Date must be from June 2017.
```

Salida de `fines_calification()` con los dos meses anteriores:

```
CALIFICACION   GRAVE    LEVE  MUY GRAVE
MES ANIO
5   2019       61124  111017        747
12  2024      157605   91388        808
```

La primera vez, cada mes se descarga de Internet y tarda un poco más en ejecutar.  
Las siguientes veces se lee de la caché local mientras no pasen los días de `obsolescence`.


### Comando

Al instalar el paquete se crea el comando `tarea-python-ucm` (definido en `[project.scripts]`):

```bash
uv run tarea-python-ucm
# tarea_python_ucm: Madrid traffic fines package.
```

### Cuadernos

- `enunciado/enunciado.ipynb`: ETAPA 1, el análisis exploratorio de diciembre de 2024.
- `enunciado/validacion.ipynb`: ejemplos de uso de todas las clases y de las excepciones `CacheError` y `MadridError`.

---

## 3. Descripción del paquete

El código y los docstrings están en inglés, con el formato Google.

### Módulo `cache`

| Elemento | Descripción |
|---|---|
| `CACHE_DIR` | Carpeta base de la caché: `Path.home() / ".my_cache"`. |
| `Cache(app_name, obsolescence)` | Guarda texto en disco en `CACHE_DIR/app_name`. Tiene las propiedades de solo lectura `app_name`, `cache_dir` y `obsolescence`, y los métodos `set`, `exists`, `load`, `how_old` (en milisegundos), `is_obsolete`, `delete` y `clear`. |
| `CacheURL(app_name, obsolescence)` | Hereda de `Cache`. Guarda cada URL con un nombre de fichero igual al hash MD5 de la URL y de sus parámetros. Redefine `exists`, `load`, `how_old`, `is_obsolete` y `delete` con `**kwargs`, y añade `get(url)`, que lee de la caché o descarga. |
| `CacheError` | Excepción para cualquier error del módulo. |

### Módulo `madridFines`

| Elemento | Descripción |
|---|---|
| `RAIZ`, `DOWNLOAD` | Raíz del portal y página de descargas de las multas. |
| `get_url(year, month)` | Devuelve la URL del CSV de ese mes, obtenida por *scraping* (requests + BeautifulSoup). |
| `MadridFines(app_name, obsolescence)` | Atributos de solo lectura `cacheurl`, `data` y `loaded`. Métodos estáticos `load` y `clean`, y métodos `add`, `clean_cache`, `fines_hour`, `fines_calification` y `total_payment`. |
| `MadridError` | Excepción para cualquier error del módulo. |

---

## 4. Tests

Están en `tests/`, fuera del paquete, y siguen los ejemplos de la asignatura (tema 8, `funciones_pk/tests`).

### Ejecución (desde la raíz del proyecto)

```bash
uv run python -m pytest -v --doctest-modules --cov=. --cov-report=html
# Informe de cobertura: abrir htmlcov/index.html
```

Otras formas:

```bash
uv run python tests/run_all_tests.py          # ejecuta todos los tests de la carpeta
uv run python tests/test_cache.py             # un fichero concreto
```

### Qué se prueba

- **`test_cache.py`:**
  - `Cache`: validación del constructor, propiedades, `__repr__`/`__str__`, guardar y leer, sobrescribir, nombres y datos inválidos, `exists`, nombres inexistentes, edad, obsolescencia, `delete` y `clear`.
  - `CacheURL`: el hash (32 caracteres, independiente del orden de los kwargs), la primera descarga, la segunda vez desde la caché (1 sola llamada), volver a descargar si está obsoleto, 404, error de red, URL no guardada y `delete`.
- **`test_madridFines.py`:**
  - `get_url`: URL de «Descarga» de diciembre de 2024 y de mayo de 2019 (la CSV, no la TXT); fechas inválidas sin llamar a la web; mes no publicado; mes sin enlace de descarga; status 500; sin red.
  - `MadridFines`:
    - constructor y propiedades (copias);
    - `load` (sin limpiar, error de descarga → `MadridError`);
    - `clean` (nombres, textos, números, coordenadas de 2019, índice `FECHA`, hora 17.06 → 17:06);
    - `add` (un mes, dos meses ordenados, duplicado, mes no disponible, año completo, reutiliza la caché);
    - `clean_cache`;
    - las tres consultas con valores exactos y sin datos.
  - `__init__.py`: `__all__` y `main()`.

---

## 5. Declaración responsable sobre autoría y uso ético de inteligencia artificial

Con la entrega de esta tarea, declaro de manera responsable que es el resultado de mi trabajo
intelectual personal y creativo, y que ha sido elaborado de acuerdo con los principios éticos y las
normas de integridad vigentes en la comunidad académica y, más específicamente, en la
[Universidad Complutense de Madrid](https://www.ucm.es/file/declaracion-responsable-sobre-autoria-y-uso-%C3%89tico-de-herramientas-de-ia).

Soy, pues, autor del material aquí incluido y, cuando no ha sido así y he tomado el material de otra
fuente, lo he citado o bien he declarado su procedencia de forma clara, incluidas, en su caso,
herramientas de inteligencia artificial. Las ideas y aportaciones principales incluidas en este
trabajo, y que acreditan la adquisición de competencias, son mías y no proceden de otras fuentes o
han sido reescritas usando material de otras fuentes.

### 5.1 Uso de inteligencia artificial

**Herramienta:** Claude (Anthropic), en la aplicación de escritorio de Claude (modo Cowork), dentro de un
proyecto de estudio de la asignatura, del 23/09/2026 al 07/10/2026.

**Cómo la he usado:**

- **Planificación:** análisis del enunciado, conocimientos necesarios, elección de cursos (DataCamp) y calendario de trabajo.
- **Tutor:**
  - Explicaciones de conceptos con ejemplos propios, por ejemplo `@staticmethod`, `rename` frente a `.str.strip()`, `pivot_table` y `unstack`, fixtures y `monkeypatch`;
  - Revisión de mi código una vez realizado, con enseñanzas como tutor de en que me debería de fijar.
  - La mayor parte del código del paquete la he escrito yo con esa ayuda: `cache.py` completo, `__init__.py`, y en `madridFines.py` `get_url`, el constructor y las propiedades, `load`, `clean`, `clean_cache`, `add`, `fines_hour` y `fines_calification`.
  - La redacción de este README, a partir de las decisiones tomadas durante el desarrollo.
- **Depuración con datos reales:** al probar `get_url` con la web real apareció un `ParserError`. La IA me ayudó a analizar la estructura de la página y propuso las correcciones:
  - El segundo bucle que busca el enlace «Descarga»;
  - El prefijo «CSV »;
  - `get_text(" ", strip=True)`;
  - `a.get("href", "")`.
- **Código generado por la IA a petición mía (Cesar Alejandro Solano Suarez):**
  - La parte de matplotlib de `fines_hour` (no había usado matplotlib antes);
  - Borradores de varios docstrings, que después he adaptado;
  - **Los tests**: gran ayuda en `tests/test_cache.py` y `tests/test_madridFines.py`, basados en los ejemplos de la profesora, de los cuales posteriormente se han revisado uno a uno y entendido el por qué de cada decisión.

Todo el código generado o propuesto por la IA lo he revisado, ejecutado con los datos reales y con
pytest, y entiendo cómo funciona. Las decisiones de diseño las he tomado yo (o venian dadas en el enunciado), así mismo como el código en **inglés**.

### 5.2 Cursos de DataCamp realizados para esta práctica

| Curso | Para qué me ha servido |
|---|---|
| [Data Manipulation with pandas](https://www.datacamp.com/courses/data-manipulation-with-pandas) | ETAPA 1 y consultas: selección y transformación de columnas, ordenación (`sort_index`), agrupaciones y `pivot_table`, gráficos con `plot`. |
| [Object-Oriented Programming in Python](https://www.datacamp.com/courses/object-oriented-programming-in-python) | Clases, herencia (`CacheURL` de `Cache`), `super()`, `__str__` / `__repr__`, atributos privados con `@property` y excepciones propias. |
| [Developing Python Packages](https://www.datacamp.com/courses/developing-python-packages) | Estructura del paquete, `__init__.py` e imports, construir y distribuir el paquete (wheel) y documentación (README, docstrings). |
| [Writing Functions in Python](https://www.datacamp.com/courses/writing-functions-in-python) | Buenas prácticas de funciones y docstrings con formato Google. |

### 5.3 Material de la asignatura (profesora Yolanda García Ruiz)

El material impartido por la profesora de la asignatura ha sido utilizado como base de la solución de la gran mayoría de métodos, clases y funciones.

### 5.4 Otras fuentes

- [Portal de datos abiertos del Ayuntamiento de Madrid](https://datos.madrid.es/dataset/210104-0-multas-circulacion-detalle/downloads): página de descargas y CSV de multas.
- Documentación oficial enlazada en el enunciado: [PEP 8](https://peps.python.org/pep-0008/), [`pathlib.Path.home`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.home) y [`BeautifulSoup`](https://beautiful-soup-4.readthedocs.io/en/latest/).
