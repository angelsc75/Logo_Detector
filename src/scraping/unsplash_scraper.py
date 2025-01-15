import logging
import requests
from .scraper_base import ImageScraperBase

# Configuración del logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class UnsplashImageScraper(ImageScraperBase):
    def __init__(self, save_dir: str, api_key: str):
        super().__init__(save_dir)
        self.api_key = api_key

    def scrape(self, query: str, limit: int = 50):
        """Realiza una búsqueda en Unsplash y descarga imágenes."""
        search_url = f"https://unsplash.com/s/photos/{query}"
        response = requests.get(search_url, headers={"Authorization": f"Client-ID {self.api_key}"})
        response.raise_for_status()
        
        images = response.json()
        count = 0

        for img in images[:limit]:
            try:
                img_url = img['urls']['regular']
                if img_url and img_url.startswith("http"):
                    filename = f"{query.replace(' ', '_')}_{count}.jpg"
                    self.save_image(img_url, filename)
                    count += 1
            except Exception as e:
                logger.error(f"Error en la imagen {count}: {e}")

    def save_image(self, img_url: str, filename: str):
        # Implementación para guardar la imagen
        pass
