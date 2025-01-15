import os
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime
import sqlite3
import json
from pytube import YouTube

class LogoDetector:
    def __init__(self, weights_path=None, data_yaml=None):
        """
        Inicializa el detector de logos
        weights_path: ruta al modelo entrenado (si existe)
        data_yaml: ruta al archivo data.yaml para entrenamiento
        """
        self.model = YOLO('yolov8n.pt')  # Comenzar con modelo pre-entrenado
        self.data_yaml = data_yaml
        self.db_path = 'detections.db'
        self.setup_database()
        
        # Verificar estructura del dataset
        self.verify_dataset_structure()
        
        if weights_path and os.path.exists(weights_path):
            try:
                self.model = YOLO(weights_path)
                print(f"Modelo cargado desde: {weights_path}")
            except Exception as e:
                print(f"Error al cargar el modelo: {str(e)}")
                print("Usando modelo base yolov8n.pt")

    def setup_database(self):
        """Configura la base de datos para guardar las detecciones"""
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
            
            # Crear tabla para las detecciones individuales
            c.execute('''CREATE TABLE IF NOT EXISTS detections
                        (video_name TEXT,
                         frame_number INTEGER,
                         brand TEXT,
                         confidence REAL,
                         bbox TEXT,
                         timestamp REAL)''')
            
            conn.commit()
            print("Base de datos configurada correctamente")
        except Exception as e:
            print(f"Error configurando la base de datos: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def verify_dataset_structure(self):
        """Verifica que la estructura del dataset sea correcta"""
        if not self.data_yaml or not os.path.exists(self.data_yaml):
            print(f"Error: No se encuentra data.yaml en {self.data_yaml}")
            return False

        # Obtener el directorio base del dataset
        dataset_dir = os.path.dirname(self.data_yaml)
        
        required_dirs = [
            os.path.join(dataset_dir, "train", "images"),
            os.path.join(dataset_dir, "train", "labels"),
            os.path.join(dataset_dir, "valid", "images"),
            os.path.join(dataset_dir, "valid", "labels"),
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
        return True

    def train(self, epochs=100, imgsz=640, batch_size=16):
        """Entrena el modelo con los parámetros especificados"""
        print("Iniciando entrenamiento...")
        try:
            self.model.train(
                data=self.data_yaml,
                epochs=epochs,
                imgsz=imgsz,
                batch=batch_size,
                name='logo_detection'
            )
            print("Entrenamiento completado!")
            
            # Cargar el mejor modelo después del entrenamiento
            best_weights_path = os.path.join('runs', 'detect', 'logo_detection', 'weights', 'best.pt')
            if os.path.exists(best_weights_path):
                self.model = YOLO(best_weights_path)
                print(f"Mejor modelo cargado desde: {best_weights_path}")
            else:
                print("Advertencia: No se encontró el archivo de mejores pesos")
        except Exception as e:
            print(f"Error durante el entrenamiento: {str(e)}")

    def process_video(self, video_path, conf_threshold=0.25):
        """Procesa un video y devuelve estadísticas de detección con visualización"""
        print(f"Procesando video: {video_path}")
        video_name = os.path.basename(video_path)
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("No se pudo abrir el video")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps
            
            detections_count = {'adidas': 0, 'puma': 0}
            frames_with_detections = {'adidas': 0, 'puma': 0}
            
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            frame_number = 0
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                timestamp = frame_number / fps
                results = self.model.predict(frame, conf=conf_threshold, verbose=False)[0]
                
                for box in results.boxes:
                    cls = results.names[int(box.cls[0])]  # Nombre de la clase detectada
                    conf = float(box.conf[0])  # Confianza de la detección
                    xyxy = box.xyxy[0].cpu().numpy()  # Coordenadas del bounding box

                    # Guardar detecciones en la base de datos
                    c.execute('''INSERT INTO detections
                                (video_name, frame_number, brand, confidence, bbox, timestamp)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                            (video_name, frame_number, cls, conf, json.dumps(xyxy.tolist()), timestamp))
                    
                    detections_count[cls] += 1
                    frames_with_detections[cls] += 1

                    # Dibujar el bounding box en el frame
                    cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (0, 255, 0), 2)

                    # Añadir el texto con el nombre de la clase y la confianza
                    label = f"{cls} {conf:.2f}"
                    cv2.putText(frame, label, (int(xyxy[0]), int(xyxy[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Mostrar el frame con detecciones
                cv2.imshow("Detections", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                frame_number += 1
                if frame_number % 100 == 0:
                    print(f"Procesados {frame_number} frames...")
            
            stats = {
                'total_frames': total_frames,
                'duration': duration,
                'detections': {
                    brand: {
                        'total_detections': count,
                        'frames_with_detections': frames_with_detections[brand],
                        'percentage_time': (frames_with_detections[brand] / total_frames) * 100
                    }
                    for brand, count in detections_count.items()
                }
            }
            
            c.execute('''INSERT INTO video_analysis
                        (video_name, analysis_date, total_frames, duration_seconds, detection_summary)
                        VALUES (?, ?, ?, ?, ?)''',
                        (video_name, datetime.now().isoformat(), total_frames, duration, json.dumps(stats)))
            
            conn.commit()
            return stats

        except Exception as e:
            print(f"Error procesando el video: {str(e)}")
            return None
        finally:
            if 'cap' in locals():
                cap.release()
            if 'conn' in locals():
                conn.close()
            cv2.destroyAllWindows()

                
    def process_youtube_video(self, youtube_url):
        """Procesa un video de YouTube"""
        try:
            yt = YouTube(youtube_url)
            print(f"Descargando video: {yt.title}")
            
            # Obtener el stream con mejor resolución
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            
            if not stream:
                raise Exception("No se encontró un stream válido")
            
            # Descargar a un archivo temporal
            temp_path = "temp_video.mp4"
            stream.download(filename=temp_path)
            
            print("Video descargado, procesando...")
            stats = self.process_video(temp_path)
            
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            return stats
            
        except Exception as e:
            print(f"Error procesando video de YouTube: {str(e)}")
            return None

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
    project_root = "C:/Users/ang01/Desktop/CURSO F5/25 Proyecto de Computer Vision/brand_detection_Angel_Leire"
    
    # Construir rutas
    data_yaml = os.path.join(project_root, "data", "dataset_yolo", "data.yaml")
    
    # Buscar el último modelo entrenado
    runs_dir = os.path.join(project_root, "runs", "detect")
    last_model = None
    if os.path.exists(runs_dir):
        # Buscar la última carpeta logo_detection con un modelo entrenado
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
    
    # Solicitar URL del video
    video_input = input("Ingresa la ruta al video local o URL de YouTube: ")
    
    # Procesar según el tipo de entrada
    if video_input.startswith(('http://', 'https://')):
        print("Procesando video de YouTube...")
        stats = detector.process_youtube_video(video_input)
    else:
        print("Procesando video local...")
        stats = detector.process_video(video_input)
    
    if stats:
        detector.generate_report(stats)
    else:
        print("Error procesando el video")

if __name__ == "__main__":
    main()