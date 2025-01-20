import streamlit as st
import os
import sys
import tempfile
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sqlite3
from datetime import datetime

# Añadir el directorio src al path de Python
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.append(src_path)

# Importar LogoDetector desde models
from models.logo_detector import LogoDetector

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
    
    # Inicializar el detector
    try:
        detector = load_detector()
        st.success("Detector inicializado correctamente")
    except Exception as e:
        st.error(f"Error al inicializar el detector: {str(e)}")
        return
    
    # Sidebar para selección de marcas y configuración
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