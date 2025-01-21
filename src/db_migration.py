# db_migration.py
import sqlite3
import os

def migrate_database(db_path):
    """
    Crea o migra la base de datos asegurando la estructura correcta
    """
    print(f"Iniciando configuración de la base de datos en: {db_path}")
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Verificar si la tabla detections existe
        c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='detections'")
        table_exists = c.fetchone()[0] > 0
        
        if table_exists:
            print("Tabla detections encontrada, verificando estructura...")
            # Verificar columnas existentes
            c.execute("PRAGMA table_info(detections)")
            existing_columns = {col[1] for col in c.fetchall()}
            
            # Si falta la columna image_path, crear respaldo y nueva tabla
            if 'image_path' not in existing_columns:
                print("Realizando migración para añadir columna image_path...")
                c.execute("CREATE TABLE detections_backup AS SELECT * FROM detections")
                c.execute("DROP TABLE detections")
                create_new_table = True
            else:
                print("La estructura de la tabla es correcta")
                create_new_table = False
        else:
            print("Tabla detections no encontrada, creando nueva tabla...")
            create_new_table = True
        
        if create_new_table:
            # Crear tabla con la estructura correcta
            c.execute('''CREATE TABLE detections
                        (video_name TEXT,
                        frame_number INTEGER,
                        brand TEXT,
                        confidence REAL,
                        bbox TEXT,
                        timestamp REAL,
                        image_path TEXT)''')
            print("Tabla detections creada con la estructura correcta")
            
            # Si había datos en backup, restaurarlos
            if table_exists:
                print("Restaurando datos desde backup...")
                c.execute("""
                    INSERT INTO detections 
                        (video_name, frame_number, brand, confidence, bbox, timestamp)
                    SELECT 
                        video_name, frame_number, brand, confidence, bbox, timestamp
                    FROM detections_backup
                """)
                c.execute("DROP TABLE detections_backup")
                print("Datos restaurados correctamente")
        
        # Crear tabla video_analysis si no existe
        c.execute('''CREATE TABLE IF NOT EXISTS video_analysis
                    (video_name TEXT,
                    analysis_date TEXT,
                    total_frames INTEGER,
                    duration_seconds REAL,
                    detection_summary TEXT)''')
        print("Tabla video_analysis verificada")
        
        # Verificar estructura final
        c.execute("PRAGMA table_info(detections)")
        print("\nEstructura final de la tabla detections:")
        for col in c.fetchall():
            print(f"- {col[1]} ({col[2]})")
        
        conn.commit()
        print("Configuración de base de datos completada con éxito")
        
    except Exception as e:
        conn.rollback()
        print(f"Error durante la configuración: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Ajusta esta ruta según tu estructura de proyecto
    DB_PATH = "../database/detections.db"
    migrate_database(DB_PATH)