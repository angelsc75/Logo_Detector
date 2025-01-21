import streamlit as st
import os
import sys
import tempfile
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime
import requests
from PIL import Image
import logging
import time

# Configuración de la página
st.set_page_config(
    page_title="Branding Eye",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar estilo personalizado
st.markdown("""
    <style>
        .main {
            background-color: #E6E6FA;
        }
        .stApp {
            background-color: #E6E6FA;
        }
        .css-1v0mbdj.etr89bj1 img {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
    </style>
""", unsafe_allow_html=True)

# Añadir el directorio src al path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar LogoDetector desde models
from models.logo_detector import LogoDetector
API_URL = os.getenv('API_URL', 'http://127.0.0.1:8000')  # Asegúrate de que FastAPI esté corriendo en esta dirección

def show_header():
    # En Docker, el logo estará en el directorio actual
    logo_path = "logo_branding_eye.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        logger.warning(f"Logo no encontrado en: {logo_path}")
    st.markdown("<h1 style='text-align: center;'>Branding Eye</h1>", unsafe_allow_html=True)
    
def load_detector():
    """Inicializa y carga el detector de logos"""
    if 'detector' not in st.session_state:
        try:
            data_yaml = os.path.join(project_root, "data", "dataset_yolo", "data.yaml")
            
            # Buscar el último modelo entrenado
            runs_dir = os.path.join(project_root, "runs", "detect")
            last_model = None
            if os.path.exists(runs_dir):
                detection_folders = [f for f in os.listdir(runs_dir) if f.startswith('logo_detection')]
                if detection_folders:
                    last_folder = sorted(detection_folders, key=lambda x: int(x.replace('logo_detection', '') or 0))[-1]
                    weights_path = os.path.join(runs_dir, last_folder, "weights", "best.pt")
                    if os.path.exists(weights_path):
                        last_model = weights_path
            
            st.session_state.detector = LogoDetector(last_model, data_yaml)
            logger.info("Detector inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar el detector: {str(e)}")
            raise e

    return st.session_state.detector
def clean_database_folder():
    """Limpia todo el contenido de la carpeta database y reinicializa la base de datos."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    database_dir = os.path.join(project_root, "database")
    
    if os.path.exists(database_dir):
        # Eliminar todos los archivos dentro de la carpeta
        for item in os.listdir(database_dir):
            item_path = os.path.join(database_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    import shutil
                    shutil.rmtree(item_path)
                logger.info(f"Eliminado: {item_path}")
            except Exception as e:
                logger.error(f"Error eliminando {item_path}: {str(e)}")
    else:
        os.makedirs(database_dir)
        logger.info(f"Creado directorio database: {database_dir}")
    
    # Crear el directorio para imágenes
    images_dir = os.path.join(database_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    logger.info(f"Creado directorio de imágenes: {images_dir}")
    
    # Reinicializar la base de datos
    db_path = os.path.join(database_dir, "detections.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Crear las tablas necesarias
    c.execute('''CREATE TABLE IF NOT EXISTS video_analysis
                (video_name TEXT,
                analysis_date TEXT,
                total_frames INTEGER,
                duration_seconds REAL,
                detection_summary TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS detections
                (video_name TEXT,
                frame_number INTEGER,
                brand TEXT,
                confidence REAL,
                bbox TEXT,
                timestamp REAL,
                image_path TEXT)''')
    
    conn.commit()
    conn.close()
    logger.info("Base de datos reinicializada correctamente")
        
def search_detections(video_name=None, brand=None):
    """Llama a la API para buscar detecciones."""
    params = {}
    if video_name:
        params["video_name"] = video_name
    if brand:
        params["brand"] = brand
    response = requests.get(f"{API_URL}/detections/", params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Error buscando detecciones")
        return []

def delete_detection(rowid):
    """Llama a la API para eliminar una detección."""
    logger.info(f"Iniciando delete_detection para rowid: {rowid}")
    
    # Verificar si ya se está procesando esta eliminación
    if 'processing_delete' not in st.session_state:
        st.session_state.processing_delete = False
        
    if st.session_state.processing_delete:
        logger.info("Evitando doble ejecución del delete")
        return False
        
    st.session_state.processing_delete = True
    
    url = f"{API_URL}/detections/{rowid}"
    logger.info(f"URL de la petición DELETE: {url}")
    
    try:
        response = requests.delete(url)
        logger.info(f"Petición DELETE enviada. Status code: {response.status_code}")
        logger.info(f"Respuesta completa: {response.text}")
        
        if response.status_code == 200:
            st.success(f"Detección {rowid} eliminada correctamente")
            # Resetear el estado y recargar
            st.session_state.processing_delete = False
            st.session_state.delete_requested = False
            st.session_state.delete_id = None
            st.rerun()
            return True
        
        st.session_state.processing_delete = False
        return False
        
    except Exception as e:
        logger.error(f"Error en delete_detection: {str(e)}")
        st.session_state.processing_delete = False
        return False

def manage_detections():
    st.header("Gestión de Detecciones")
    
    # Variables de estado para controlar el borrado
    if 'delete_requested' not in st.session_state:
        st.session_state.delete_requested = False
    if 'delete_id' not in st.session_state:
        st.session_state.delete_id = None
    if 'processing_delete' not in st.session_state:
        st.session_state.processing_delete = False

    # Función para manejar el click del botón
    def request_delete(rowid):
        if not st.session_state.processing_delete:
            st.session_state.delete_requested = True
            st.session_state.delete_id = rowid
            logger.info(f"Delete solicitado para rowid: {rowid}")

    # Formulario de búsqueda
    video_name = st.text_input("Nombre del video (opcional)")
    brand = st.selectbox("Marca", ["", "adidas", "nike", "puma"], index=0)
    
    if st.button("Buscar detecciones"):
        logger.info("Botón de búsqueda presionado")
        detections = search_detections(video_name, brand)
        
        if detections:
            for detection in detections:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                            **ID:** {detection['rowid']}  
                            **Marca:** {detection['brand']}  
                            **Frame:** {detection['frame_number']}  
                            **Confianza:** {detection['confidence']:.2f}
                        """)
                        
                        if detection['image_path']:
                            try:
                                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                image_path = os.path.join(base_path, "database", "images", 
                                                        os.path.basename(detection['image_path']))
                                
                                if os.path.exists(image_path):
                                    image = Image.open(image_path)
                                    st.image(image, 
                                           caption=f"Detección de {detection['brand']} (Frame {detection['frame_number']})",
                                           use_container_width=True)
                                    image.close()
                            except Exception as e:
                                logger.error(f"Error al cargar la imagen: {str(e)}")
                    
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"delete_{detection['rowid']}", 
                                   on_click=request_delete, args=(detection['rowid'],)):
                            logger.info(f"Botón de eliminar presionado para rowid: {detection['rowid']}")

                    st.markdown("---")
        else:
            st.info("No se encontraron detecciones.")

    # Procesar la eliminación si fue solicitada
    if st.session_state.delete_requested and not st.session_state.processing_delete:
        logger.info(f"Procesando solicitud de eliminación para rowid: {st.session_state.delete_id}")
        if delete_detection(st.session_state.delete_id):
            st.session_state.delete_requested = False
            st.session_state.delete_id = None
            st.session_state.processing_delete = False
        else:
            st.error("Error al eliminar la detección")
            st.session_state.delete_requested = False
            st.session_state.delete_id = None
            st.session_state.processing_delete = False
            
def load_detector():
    """Inicializa y carga el detector de logos"""
    data_yaml = os.path.join(project_root, "data", "dataset_yolo", "data.yaml")
    
    # Buscar el último modelo entrenado
    runs_dir = os.path.join(project_root, "runs", "detect")
    last_model = None
    if os.path.exists(runs_dir):
        detection_folders = [f for f in os.listdir(runs_dir) if f.startswith('logo_detection')]
        if detection_folders:
            last_folder = sorted(detection_folders, key=lambda x: int(x.replace('logo_detection', '') or 0))[-1]
            weights_path = os.path.join(runs_dir, last_folder, "weights", "best.pt")
            if os.path.exists(weights_path):
                last_model = weights_path
    
    return LogoDetector(last_model, data_yaml)

def plot_brand_timeline(video_name, db_path):
    """Genera un gráfico de líneas mostrando las detecciones a lo largo del tiempo"""
    conn = sqlite3.connect(db_path)
    query = """
    SELECT brand, timestamp, confidence
    FROM detections
    WHERE video_name = ?
    ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn, params=(video_name,))
    conn.close()
    
    if df.empty:
        return None
        
    fig = px.line(df, x='timestamp', y='confidence', color='brand',
                  title='Detección de logos a lo largo del tiempo',
                  labels={'timestamp': 'Tiempo (segundos)',
                         'confidence': 'Confianza',
                         'brand': 'Marca'})
    return fig

def plot_brand_summary(stats):
    """Genera dos gráficos: un gráfico de barras para las detecciones totales
    y un gráfico circular para los porcentajes de tiempo en pantalla."""
    
    brands = []
    percentages = []
    detections = []
    
    for brand, data in stats['detections'].items():
        brands.append(brand)
        percentages.append(data['percentage_time'])
        detections.append(data['total_detections'])
    
    # Crear la figura con dos subplots
    fig = go.Figure()
    
    # Configurar el layout para dos gráficos lado a lado
    fig = go.Figure()
    
    # Gráfico de barras para total de detecciones
    fig.add_trace(
        go.Bar(
            x=brands,
            y=detections,
            name='Total detecciones',
            text=detections,
            textposition='auto',
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']  # Colores distintos para cada marca
        )
    )
    
    # Gráfico circular para porcentajes
    fig.add_trace(
        go.Pie(
            labels=brands,
            values=percentages,
            name='Tiempo en pantalla',
            domain={'x': [0.6, 1]},  # Posicionar el pie chart en la parte derecha
            hole=0.4,  # Hacer un donut chart
            textinfo='label+percent',
            textposition='auto',
            marker=dict(colors=['#1f77b4', '#ff7f0e', '#2ca02c'])
        )
    )
    
    # Actualizar el layout
    fig.update_layout(
        title='Análisis de Detecciones por Marca',
        showlegend=False,
        # Ajustar el gráfico de barras al lado izquierdo
        barmode='group',
        xaxis=dict(domain=[0, 0.5]),
        # Configuración general
        height=500,
        margin=dict(t=50, l=50, r=50, b=50),
        # Títulos de los ejes para el gráfico de barras
        xaxis_title="Marcas",
        yaxis_title="Número de detecciones"
    )
    
    # Actualizar el diseño de las barras
    fig.update_traces(
        selector=dict(type='bar'),
        texttemplate='%{text:,}',  # Formato con separador de miles
        textposition='auto'
    )
    
    return fig

def main():
    # Mostrar header con logo
    show_header()

    # Sidebar para navegación y acciones
    st.sidebar.title("Menú")
    
    # Botón para limpiar la base de datos
    if st.sidebar.button("🗑️ Limpiar Base de Datos"):
        with st.spinner("Limpiando base de datos..."):
            clean_database_folder()
            # Reinicializar el detector
            if 'detector' in st.session_state:
                st.session_state.detector.setup_database()
        st.sidebar.success("Base de datos limpiada correctamente")
        
    # Selección de modo
    app_mode = st.sidebar.radio(
        "Selecciona una funcionalidad",
        ["Procesar Video", "Gestión de Detecciones"]
    )

    # Inicializar el detector (ahora solo una vez)
    try:
        detector = load_detector()
    except Exception as e:
        st.error(f"Error al inicializar el detector: {str(e)}")
        return

    if app_mode == "Procesar Video":
        process_video_logic(detector)
    elif app_mode == "Gestión de Detecciones":
        manage_detections()


def process_video_logic(detector):
    """Lógica para la funcionalidad de procesamiento de videos."""
    st.sidebar.header("Configuración")

    # Selección de marcas
    available_brands = ['adidas', 'nike', 'puma']
    selected_brands = st.sidebar.multiselect(
        "Seleccionar marcas a detectar",
        available_brands,
        default=available_brands
    )

    # Umbrales de confianza solo para las marcas seleccionadas
    conf_thresholds = {}
    if selected_brands:
        st.sidebar.header("Umbrales de confianza")
        for brand in selected_brands:
            conf_thresholds[brand] = st.sidebar.slider(
                f"Umbral de confianza para {brand.upper()}",
                min_value=0.0,
                max_value=1.0,
                value=0.5,
                step=0.05,
                key=f"conf_{brand}"
            )

    # Subir video
    uploaded_file = st.file_uploader("Selecciona un video", type=['mp4', 'avi', 'mov'])
    if uploaded_file:
        # Guardar el archivo subido temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name

        process_button = st.button("Procesar video")
        if process_button:
            if not selected_brands:
                st.error("Por favor, selecciona al menos una marca para detectar")
            else:
                try:
                    with st.spinner("Procesando video..."):
                        stats = detector.process_video(video_path, conf_thresholds)
                        if stats:
                            st.success("¡Video procesado exitosamente!")

                            # Mostrar gráficas
                            st.subheader("Análisis de detecciones")

                            # Gráfico de resumen
                            fig_summary = plot_brand_summary(stats)
                            st.plotly_chart(fig_summary)

                            # Gráfico de línea temporal
                            fig_timeline = plot_brand_timeline(uploaded_file.name, detector.db_path)
                            if fig_timeline:
                                st.plotly_chart(fig_timeline)

                            # Mostrar estadísticas detalladas
                            st.subheader("Estadísticas detalladas")
                            st.json(stats)
                        else:
                            st.error("Error al procesar el video")
                except Exception as e:
                    st.error(f"Error durante el procesamiento: {str(e)}")
                    logger.error(f"Error detallado: {str(e)}")
                finally:
                    # Limpiar archivo temporal
                    os.unlink(video_path)


if __name__ == "__main__":
    main()