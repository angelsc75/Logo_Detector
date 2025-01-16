from abc import ABC, abstractmethod
import os
import requests
from io import BytesIO
from PIL import Image
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageScraperBase(ABC):
    def __init__(self, save_dir: str):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)

    @abstractmethod
    def scrape(self, query: str, limit: int):
        """Método abstracto que debe ser implementado por las clases hijas."""
        pass

    def save_image(self, image_url: str, filename: str):
        """Guarda una imagen desde una URL en la carpeta especificada."""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img.save(os.path.join(self.save_dir, filename))
            logger.info(f"Imagen guardada: {filename}")
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")
