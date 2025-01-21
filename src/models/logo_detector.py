import os
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime
import sqlite3
import json

class LogoDetector:
    def __init__(self, weights_path=None, data_yaml=None):
        """
        Inicializa el detector de logos
        weights_path: ruta al modelo entrenado (si existe)
        data_yaml: ruta al archivo data.yaml para entrenamiento
        """
        self.model = YOLO('yolov8n.pt')  # Comenzar con modelo pre-entrenado
        self.data_yaml = data_yaml
        
        # Imprimir la ruta actual para debugging
        print(f"Directorio actual: {os.getcwd()}")
        
        # Configurar ruta de la base de datos al mismo nivel que data
        if data_yaml:
            # Obtener la ruta al directorio 'data'
            data_dir = os.path.dirname(os.path.dirname(self.data_yaml))
            # La base de datos debe estar al mismo nivel que 'data'
            project_root = os.path.dirname(data_dir)
        else:
            project_root = os.getcwd()  # Usar directorio actual como fallback
            
        print(f"Raíz del proyecto detectada: {project_root}")
        
        # Ahora database estará al mismo nivel que data
        database_dir = os.path.join(project_root, "database")
        self.db_path = os.path.join(database_dir, "detections.db")
        
        print(f"Ruta de la base de datos: {self.db_path}")
        # Limpiar base de datos y carpeta de imágenes al inicio
                
        # Crear el directorio database si no existe
        if not os.path.exists(database_dir):
            os.makedirs(database_dir)
            print(f"Directorio de base de datos creado: {database_dir}")
            
        self.setup_database()
        
        self.verify_dataset_structure()
        
        if weights_path and os.path.exists(weights_path):
            try:
                self.model = YOLO(weights_path)
                print(f"Modelo cargado desde: {weights_path}")
            except Exception as e:
                print(f"Error al cargar el modelo: {str(e)}")
                print("Usando modelo base yolov8n.pt")

    def verify_dataset_structure(self):
        """Verifica que la estructura del dataset sea correcta"""
        if not self.data_yaml or not os.path.exists(self.data_yaml):
            print(f"Error: No se encuentra data.yaml en {self.data_yaml}")
            return False

        dataset_dir = os.path.dirname(self.data_yaml)
        print(f"Verificando estructura del dataset en: {dataset_dir}")
        
        required_dirs = [
            os.path.join(dataset_dir, "train", "images"),
            os.path.join(dataset_dir, "train", "labels"),
            os.path.join(dataset_dir, "val", "images"),
            os.path.join(dataset_dir, "val", "labels"),
            os.path.join(dataset_dir, "test", "images"),
            os.path.join(dataset_dir, "test", "labels")
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_path)
                try:
                    os.makedirs(dir_path)
                    print(f"Creado directorio: {dir_path}")
                except Exception as e:
                    print(f"Error creando directorio {dir_path}: {str(e)}")

        if missing_dirs:
            print("\nDirectorios faltantes que fueron creados:")
            for dir_path in missing_dirs:
                print(f"- {dir_path}")
            print("\nPor favor, asegúrate de colocar las imágenes y etiquetas correspondientes en estos directorios.")
            return False
        print("Estructura del dataset verificada correctamente")
        return True
    
            
    def setup_database(self):
        """Configura la base de datos para guardar las detecciones."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Crear tabla para los análisis de videos
            c.execute('''CREATE TABLE IF NOT EXISTS video_analysis
                        (video_name TEXT,
                        analysis_date TEXT,
                        total_frames INTEGER,
                        duration_seconds REAL,
                        detection_summary TEXT)''')
            
            # Crear tabla detections con la estructura completa
            c.execute('''CREATE TABLE IF NOT EXISTS detections
                        (video_name TEXT,
                        frame_number INTEGER,
                        brand TEXT,
                        confidence REAL,
                        bbox TEXT,
                        timestamp REAL,
                        image_path TEXT)''')
            
            # Verificar la estructura
            c.execute("PRAGMA table_info(detections)")
            columns = {col[1] for col in c.fetchall()}
            
            required_columns = {
                'video_name', 'frame_number', 'brand', 
                'confidence', 'bbox', 'timestamp', 'image_path'
            }
            
            if columns != required_columns:
                print("La estructura de la tabla no es correcta. Ejecutando migración...")
                conn.close()
                
                # Importar y ejecutar la migración
                import db_migration
                db_migration.migrate_database(self.db_path)
                return
            
            conn.commit()
            print("Base de datos configurada correctamente")
            
        except sqlite3.OperationalError as e:
            print(f"Error configurando la base de datos: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()


    def process_video(self, video_path, conf_thresholds={'adidas': 0.50, 'nike': 0.50, 'puma': 0.50}):
        """Procesa un video y devuelve estadísticas de detección con visualización"""
        print(f"Procesando video: {video_path}")
        video_name = os.path.basename(video_path)

        # Crear directorio para las imágenes si no existe
        images_dir = os.path.join(os.path.dirname(self.db_path), "images")
        os.makedirs(images_dir, exist_ok=True)
        print(f"Directorio de imágenes: {images_dir}")

        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("No se pudo abrir el video")

            # Crear ventana para visualización
            cv2.namedWindow('Detecciones', cv2.WINDOW_NORMAL)
            
            # Obtener propiedades del video para el video de salida
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # Configurar el video de salida
            output_path = os.path.join(os.path.dirname(self.db_path), "processed_videos")
            os.makedirs(output_path, exist_ok=True)
            output_video = os.path.join(output_path, f"processed_{video_name}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_video, fourcc, fps, (frame_width, frame_height))

            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = total_frames / fps
                
                # Inicializar contadores
                detections_count = {brand: 0 for brand in conf_thresholds.keys()}
                frames_with_detections = {brand: 0 for brand in conf_thresholds.keys()}

                frame_number = 0
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break

                    timestamp = frame_number / fps
                    frame_with_boxes = frame.copy()

                    # Usar el valor mínimo de confianza para la predicción inicial
                    min_conf = float(min(conf_thresholds.values()))
                    results = self.model.predict(frame, conf=min_conf, verbose=False)[0]

                    frame_detections = {brand: False for brand in detections_count.keys()}

                    # Procesar cada detección
                    for box in results.boxes:
                        try:
                            cls_idx = int(box.cls[0])
                            cls = results.names[cls_idx]
                            conf = float(box.conf[0])

                            if cls not in conf_thresholds or conf < conf_thresholds[cls]:
                                continue

                            xyxy = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = map(int, xyxy)

                            # Dibujar bounding box y etiqueta
                            cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            label = f"{cls}: {conf:.2f}"
                            cv2.putText(frame_with_boxes, label, (x1, y1-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                            # Extraer y guardar la imagen del bounding box
                            bbox_image = frame[y1:y2, x1:x2]
                            if bbox_image.size > 0:
                                image_filename = f"{video_name}_frame{frame_number}_brand{cls}_{conf:.2f}.jpg"
                                image_path = os.path.join(images_dir, image_filename)
                                cv2.imwrite(image_path, bbox_image)

                            # Guardar detección en la base de datos
                            c.execute('''INSERT INTO detections
                                        (video_name, frame_number, brand, confidence, bbox, timestamp, image_path)
                                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                    (video_name, frame_number, cls, conf, 
                                    json.dumps(xyxy.tolist()), timestamp, image_filename))
                            conn.commit()

                            # Actualizar contadores
                            detections_count[cls] += 1
                            frame_detections[cls] = True

                        except Exception as e:
                            print(f"Error procesando detección: {str(e)}")
                            continue

                    # Actualizar frames_with_detections
                    for brand, detected in frame_detections.items():
                        if detected:
                            frames_with_detections[brand] += 1

                    # Mostrar el frame con las detecciones
                    cv2.imshow('Detecciones', frame_with_boxes)
                    out.write(frame_with_boxes)

                    # Permitir salir con 'q'
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                    frame_number += 1
                    if frame_number % 100 == 0:
                        print(f"Procesados {frame_number}/{total_frames} frames...")

                stats = {
                    'total_frames': total_frames,
                    'duration': duration,
                    'thresholds_used': conf_thresholds,
                    'detections': {
                        brand: {
                            'total_detections': count,
                            'frames_with_detections': frames_with_detections[brand],
                            'percentage_time': (frames_with_detections[brand] / total_frames) * 100
                        }
                        for brand, count in detections_count.items()
                    }
                }

                return stats

            except Exception as e:
                print(f"Error procesando el video: {str(e)}")
                return None
            finally:
                if 'conn' in locals():
                    conn.close()
                if 'out' in locals():
                    out.release()

        except Exception as e:
            print(f"Error procesando el video: {str(e)}")
            return None
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()

    def generate_report(self, stats):
        """Genera un informe legible de las estadísticas"""
        if not stats:
            print("No hay estadísticas disponibles para generar el informe")
            return

        print("\n=== INFORME DE DETECCIÓN DE LOGOS ===")
        print(f"Duración del video: {stats['duration']:.2f} segundos")
        print(f"Frames totales: {stats['total_frames']}")
        print("\nEstadísticas por marca:")
        
        for brand, brand_stats in stats['detections'].items():
            print(f"\n{brand.upper()}:")
            print(f"- Detecciones totales: {brand_stats['total_detections']}")
            print(f"- Frames con detecciones: {brand_stats['frames_with_detections']}")
            print(f"- Porcentaje de tiempo en pantalla: {brand_stats['percentage_time']:.2f}%")

def main():
    # Ruta base del proyecto
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Construir rutas
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

    print(f"Usando data.yaml en: {data_yaml}")
    if last_model:
        print(f"Usando último modelo entrenado en: {last_model}")
    
    # Inicializar detector
    detector = LogoDetector(last_model, data_yaml)
    
    # Solo entrenar si no se encuentra ningún modelo
    if not last_model:
        print("No se encontró ningún modelo entrenado. Iniciando entrenamiento...")
        if detector.verify_dataset_structure():
            detector.train()
        else:
            print("Por favor, corrige la estructura del dataset antes de entrenar")
            return
    
    # Solicitar ruta del video
    video_path = input("Ingresa la ruta al video local: ")
    
    # Procesar video
    print("Procesando video local...")
    stats = detector.process_video(video_path)
    
    if stats:
        detector.generate_report(stats)
    else:
        print("Error procesando el video")

if __name__ == "__main__":
    main()