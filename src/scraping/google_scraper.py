from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import requests
from io import BytesIO
from PIL import Image
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleImageScraper:
    def __init__(self, save_dir: str, driver_path: str = "chromedriver"):
        self.save_dir = os.path.abspath(save_dir)  # Asegúrate de usar una ruta absoluta
        os.makedirs(self.save_dir, exist_ok=True)
        logger.info(f"Guardando imágenes en: {self.save_dir}")

        # Configuración del navegador Chrome
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

        # Inicializar el driver de Chrome
        self.driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)

    def scrape(self, query: str, limit: int = 50):
        """Realiza una búsqueda en Google Images y descarga imágenes."""
        search_url = f"https://www.google.com/search?tbm=isch&q={query}+logo+transparent"
        self.driver.get(search_url)

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img.Q4LuWd"))
        )

        images = self.driver.find_elements(By.CSS_SELECTOR, "img.Q4LuWd")
        logger.info(f"Se encontraron {len(images)} imágenes.")
        count = 0

        for img in images[:limit]:
            try:
                img_url = img.get_attribute("src")
                if img_url and img_url.startswith("http"):
                    filename = f"{query.replace(' ', '_')}_{count}.jpg"
                    self.save_image(img_url, filename)
                    count += 1
            except Exception as e:
                logger.error(f"Error en la imagen {count}: {e}")

        self.driver.quit()
        logger.info(f"Se descargaron {count} imágenes de {query}.")

    def save_image(self, img_url: str, filename: str):
        try:
            logger.info(f"Descargando: {img_url}")
            response = requests.get(img_url)
            response.raise_for_status()
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img.save(os.path.join(self.save_dir, filename))
            logger.info(f"Imagen guardada: {filename}")
        except Exception as e:
            logger.error(f"Error al guardar la imagen: {e}")


