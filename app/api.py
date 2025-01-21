from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import sqlite3
from typing import Optional, List
import logging
from datetime import datetime
import os
from fastapi.middleware.cors import CORSMiddleware

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DB_PATH = "../database/detections.db"

class DeleteRequest(BaseModel):
    rowid: int

class Detection(BaseModel):
    rowid: int
    video_name: str
    frame_number: int
    brand: str
    confidence: float
    bbox: str
    timestamp: float
    image_path: Optional[str]

# Obtener la ruta absoluta al directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))
# Subir un nivel para llegar a la raíz del proyecto
project_root = os.path.dirname(current_dir)
# Configurar la ruta de la base de datos
DB_PATH = os.path.join(project_root, "database", "detections.db")

# Añadir logging para debug
logger.info(f"Usando base de datos en: {DB_PATH}")

def get_db_connection():
    try:
        if not os.path.exists(DB_PATH):
            logger.error(f"Base de datos no encontrada en: {DB_PATH}")
            raise HTTPException(status_code=500, detail="Base de datos no encontrada")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        logger.info("Conexión a base de datos establecida")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error de conexión a la base de datos: {str(e)}")

@app.get("/detections/")
async def get_detections(
    video_name: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    frame_start: Optional[int] = Query(None, ge=0),
    frame_end: Optional[int] = Query(None, ge=0)
):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si hay registros en la tabla
        cursor.execute("SELECT COUNT(*) FROM detections")
        count = cursor.fetchone()[0]
        logger.info(f"Total de registros en la base de datos: {count}")
        
        query = """
            SELECT 
                rowid, 
                video_name, 
                frame_number, 
                brand, 
                confidence, 
                bbox, 
                timestamp, 
                image_path 
            FROM detections 
            WHERE 1=1
        """
        params = []

        if video_name:
            query += " AND video_name LIKE ?"
            params.append(f"%{video_name}%")
        
        if brand:
            query += " AND brand = ?"
            params.append(brand)
        
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(min_confidence)
        
        if frame_start is not None:
            query += " AND frame_number >= ?"
            params.append(frame_start)
        
        if frame_end is not None:
            query += " AND frame_number <= ?"
            params.append(frame_end)

        query += " ORDER BY timestamp"
        
        logger.info(f"Ejecutando query: {query}")
        logger.info(f"Parámetros: {params}")
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        logger.info(f"Resultados encontrados: {len(results)}")
        
        detections = []
        for row in results:
            detection = dict(row)
            detection['confidence'] = float(detection['confidence'])
            detection['timestamp'] = float(detection['timestamp'])
            detection['frame_number'] = int(detection['frame_number'])
            detection['rowid'] = int(detection['rowid'])
            detections.append(detection)
        
        return JSONResponse(content=detections)

    except sqlite3.Error as e:
        logger.error(f"Error en la base de datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

@app.delete("/detections/{rowid}")
async def delete_detection(rowid: int):
    logger.info(f"Recibida petición DELETE para rowid: {rowid}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar si existe la detección
        cursor.execute("SELECT COUNT(*) FROM detections WHERE rowid = ?", (rowid,))
        if cursor.fetchone()[0] == 0:
            logger.warning(f"No se encontró la detección con rowid {rowid}")
            raise HTTPException(status_code=404, detail="Detección no encontrada")
        
        # Ejecutar el borrado
        cursor.execute("DELETE FROM detections WHERE rowid = ?", (rowid,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        logger.info(f"Detección {rowid} eliminada. Filas afectadas: {deleted_count}")
        return {"message": f"Detección {rowid} eliminada", "rows_affected": deleted_count}

    except sqlite3.Error as e:
        logger.error(f"Error de base de datos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'conn' in locals():
            conn.close()