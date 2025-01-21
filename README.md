# brand_detection_Angel_Leire# Detección de Marcas en Videos e Imágenes

Este proyecto implementa un sistema de detección de marcas en videos e imágenes, con conexión a una base de datos y una API desarrollada con FastAPI. Además, incluye una interfaz interactiva basada en Streamlit para gestionar y visualizar los resultados de detección.

## Características Principales

- **Procesamiento de Datos**: Preparación del dataset en formato YOLO a partir de anotaciones XML.
- **Detección de Logos**: Uso de modelos YOLO para detectar logos de marcas como Adidas, Nike y Puma en videos.
- **Gestor de Detecciones**: API RESTful para gestionar registros en la base de datos.
- **Interfaz Gráfica**: Aplicación de Streamlit para visualizar resultados, eliminar detecciones y analizar datos.
- **Base de Datos**: Almacenamiento de las detecciones en una base de datos SQLite.

## Estructura del Proyecto

```
brand_detection_Angel_Leire
    ├── app
    │   ├── api.py
    │   ├── config.py
    │   ├── core
    │   │   └── reporting
    │   ├── __init__.py
    │   └── streamlit_app.py
    ├── data
    │   ├── dataset_yolo
    │   │   └── data.yaml
    │   ├── metodos_data
    │   │   ├── dataset_organaizer.py
    │   │   ├── __init__.py
    │   │   ├── labeling.py
    │   │   ├── nombrado_archivos.py
    │   │   ├── scrape_logos.py
    │   │   └── xml_to_yolo.py
    │   ├── preparar_data_set.py
    │   ├── raw
    │   │   ├── images
    │   │   └── videos
    │   ├── test
    │   │   ├── images
    │   │   └── labels
    │   ├── train
    │   │   ├── images
    │   │   ├── labels
    │   │   └── labels.cache
    │   └── val
    │       ├── images
    │       ├── labels
    │       └── labels.cache
    ├── deployment
    │   ├── ci_cd
    │   └── cloud
    ├── docker-compose.yml
    ├── Dockerfile
    ├── frontend
    ├── models
    │   ├── best_model.pth
    │   ├── confusion_matrix.png
    │   ├── evaluation_report.txt
    │   ├── __init__.py
    │   ├── logo_detector.py
    │   └── plots
    │       └── training_results.png
    ├── notebooks
    ├── README.md
    ├── requirements.txt
    ├── scripts
    ├── src
    │   ├── api
    │   │   ├── __init__.py
    │   │   ├── main.py
    │   │   ├── routes
    │   │   ├── schemas
    │   │   └── services
    │   ├── config
    │   ├── db_migration.py
    │   ├── models
    │   ├── scraping
    │   └── utils
    │       ├── helpers.py
    │       └── __init__.py
    ├── test
    │   ├── conftest.py
    │   ├── __init__.py
    │   ├── test_api.py
    │   ├── test_detection.py
    │   ├── test_labeling.py
    │   ├── test_reporting.py
    │   └── test_video.py
    ├── venv
    │   ├── etc
    │   │   └── jupyter
    │   ├── lib64 -> lib
    │   ├── pyvenv.cfg
    │   └── share
    │       ├── jupyter
    │       └── man
    └── videos
```

## Requisitos

- **Python 3.8 o superior**
- Bibliotecas requeridas:
  - `FastAPI`
  - `Streamlit`
  - `SQLite`
  - `Plotly`
  - `Pandas`
  - `Pillow`
  - `requests`

## Instalación

1. Clona este repositorio:
   ```bash
   git clone <repositorio>
   cd <repositorio>
   ```

2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Asegúrate de que la base de datos esté disponible en `database/detections.db`.

## Uso

### 1. Preparar el Dataset

Ejecuta el script `preparar_data_set.py` para generar el dataset en formato YOLO:
```bash
python src/preparar_data_set.py
```

### 2. Ejecutar la API

Inicia el servidor FastAPI para gestionar detecciones:
```bash
uvicorn src.api:app --reload
```

### 3. Ejecutar la Aplicación Streamlit

Ejecuta la interfaz de usuario para gestionar y analizar las detecciones:
```bash
streamlit run src/streamlit_app.py
```

### 4. Procesar Videos

Desde la aplicación de Streamlit, selecciona "Procesar Video" en el menú lateral. Sube un video y configura las marcas y umbrales de confianza deseados.

### 5. Gestionar Detecciones

Usa la sección "Gestión de Detecciones" en Streamlit para buscar, visualizar y eliminar detecciones almacenadas en la base de datos.

## API Endpoints

- **GET /detections/**: Devuelve las detecciones filtradas según los parámetros especificados.
- **DELETE /detections/{rowid}**: Elimina una detección por su ID.

Consulta la documentación completa de la API en:
```
http://127.0.0.1:8000/docs
```

## Personalización

- **Marcas Detectables**: Modifica las marcas en `preparar_data_set.py` y en la configuración del modelo YOLO para añadir o eliminar marcas detectables.
- **Modelos**: Coloca nuevos modelos entrenados en `runs/detect` y actualiza la configuración si es necesario.
- **Interfaz**: Personaliza la aplicación Streamlit modificando `streamlit_app.py`.

## Contribución
Si deseas contribuir al proyecto:

- Fork el repositorio
- Crea una rama para tu funcionalidad
- Realiza tus cambios
- Envía un pull request


## Contacto
Para preguntas o sugerencias, por favor abre un issue en el repositorio.

## Autores

- Leire y equipo (Pair Programming).
