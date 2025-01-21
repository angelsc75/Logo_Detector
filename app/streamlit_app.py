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
API_URL = "http://127.0.0.1:8000"  # Asegúrate de que FastAPI esté corriendo en esta dirección

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
    try:
        # Agregar logging para debug
        logger.info(f"Intentando eliminar detección {rowid}")
        
        response = requests.delete(f"{API_URL}/detections/{rowid}")
        
        # Log de la respuesta
        logger.info(f"Respuesta del servidor: Status={response.status_code}, Content={response.text}")
        
        if response.status_code == 200:
            st.success(f"Detección {rowid} eliminada correctamente")
            # Forzar refresco de la página después de un pequeño delay
            time.sleep(0.5)  # Pequeña pausa para asegurar que la UI se actualice
            st.experimental_rerun()
            return True
        else:
            error_msg = f"Error al eliminar la detección. Status: {response.status_code}"
            if response.text:
                try:
                    error_msg += f". Detalle: {response.json()['detail']}"
                except:
                    error_msg += f". Respuesta: {response.text}"
            logger.error(error_msg)
            st.error(error_msg)
            return False
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error de conexión al intentar eliminar la detección: {str(e)}"
        logger.error(error_msg)
        st.error(error_msg)
        return False

def manage_detections():
    st.header("Gestión de Detecciones")

    # Formulario de búsqueda
    video_name = st.text_input("Nombre del video (opcional)")
    brand = st.selectbox("Marca", ["", "adidas", "nike", "puma"], index=0)
    
    search_clicked = st.button("Buscar detecciones")
    
    if search_clicked:
        try:
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
                                    
                                    logger.info(f"Intentando cargar imagen desde: {image_path}")
                                    
                                    if os.path.exists(image_path):
                                        image = Image.open(image_path)
                                        # Cambio de use_column_width a use_container_width
                                        st.image(image, 
                                               caption=f"Detección de {detection['brand']} (Frame {detection['frame_number']})",
                                               use_container_width=True)
                                        image.close()
                                    else:
                                        logger.warning(f"Archivo de imagen no encontrado: {image_path}")
                                        st.warning("Imagen no disponible")
                                except Exception as e:
                                    logger.error(f"Error al cargar la imagen: {str(e)}")
                                    st.error("Error al cargar la imagen")
                        
                        with col2:
                            if st.button("🗑️ Eliminar", key=f"delete_{detection['rowid']}"):
                                logger.info(f"Se hizo clic en el botón para rowid {detection['rowid']}")
                                if delete_detection(detection['rowid']):
                                    st.success(f"Detección {detection['rowid']} eliminada")

                        
                        st.markdown("---")
            else:
                st.info("No se encontraron detecciones.")
        except Exception as e:
            logger.error(f"Error en manage_detections: {str(e)}")
            st.error(f"Error inesperado: {str(e)}")
            
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
    """Genera un gráfico de barras con el resumen de detecciones"""
    brands = []
    percentages = []
    detections = []
    
    for brand, data in stats['detections'].items():
        brands.append(brand)
        percentages.append(data['percentage_time'])
        detections.append(data['total_detections'])
    
    fig = go.Figure(data=[
        go.Bar(name='Tiempo en pantalla (%)', x=brands, y=percentages),
        go.Bar(name='Total detecciones', x=brands, y=detections)
    ])
    
    fig.update_layout(
        title='Resumen de detecciones por marca',
        barmode='group',
        yaxis_title='Valores',
        xaxis_title='Marcas'
    )
    
    return fig

def main():
    st.title("Detector de Logos en Videos")

    # Sidebar para navegación
    st.sidebar.title("Menú")
    app_mode = st.sidebar.radio(
        "Selecciona una funcionalidad",
        ["Procesar Video", "Gestión de Detecciones"]
    )

    # Inicializar el detector
    try:
        detector = load_detector()
        st.success("Detector inicializado correctamente")
    except Exception as e:
        st.error(f"Error al inicializar el detector: {str(e)}")
        return

    if app_mode == "Procesar Video":
        # Lógica para procesar video
        process_video_logic(detector)
    elif app_mode == "Gestión de Detecciones":
        # Llamar a manage_detections
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

                # Limpiar archivo temporal
                os.unlink(video_path)

if __name__ == "__main__":
    main()
    