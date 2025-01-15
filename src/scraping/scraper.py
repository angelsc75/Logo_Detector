import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from pathlib import Path
from typing import List
from .config import SEARCH_QUERIES, SAVE_DIR

class ImageScraper:
    def __init__(self):
        self.save_dir = Path(SAVE_DIR)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Configurar Chrome
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')  # Ejecutar sin interfaz gráfica
        
    def create_folder(self, brand: str) -> Path:
        """Crear carpeta para guardar las imágenes."""
        folder_path = self.save_dir / brand
        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path

    def download_image(self, url: str, folder_path: Path, filename: str) -> bool:
        """Descargar una imagen desde una URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                file_path = folder_path / filename
                file_path.write_bytes(response.content)
                print(f"Imagen descargada: {filename}")
                return True
            return False
        except Exception as e:
            print(f"Error descargando imagen: {e}")
            return False

    def scrape_images(self, brand: str, limit: int = 30) -> List[str]:
        """Scrapear imágenes de Google Images para una marca."""
        downloaded_images = []
        folder_path = self.create_folder(brand)
        
        # Obtener términos de búsqueda para la marca
        search_terms = SEARCH_QUERIES.get(brand, [f"{brand} logo"])
        
        driver = webdriver.Chrome(options=self.options)
        
        try:
            for search_term in search_terms:
                if len(downloaded_images) >= limit:
                    break
                    
                print(f"Buscando: {search_term}")
                search_url = f"https://www.google.com/search?q={search_term}&tbm=isch"
                driver.get(search_url)
                
                # Dar tiempo para que carguen las imágenes
                time.sleep(2)
                
                # Encontrar elementos de imagen
                img_elements = driver.find_elements(By.CSS_SELECTOR, 'img.rg_i')
                
                for idx, img in enumerate(img_elements):
                    if len(downloaded_images) >= limit:
                        break
                        
                    try:
                        # Hacer click en la imagen para obtener la versión de alta resolución
                        img.click()
                        time.sleep(1)
                        
                        # Esperar y obtener la imagen en alta resolución
                        actual_image = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'img.r48jcc'))
                        )
                        
                        img_url = actual_image.get_attribute('src')
                        if img_url and img_url.startswith('http'):
                            filename = f"{brand}_logo_{len(downloaded_images)}.jpg"
                            if self.download_image(img_url, folder_path, filename):
                                downloaded_images.append(str(folder_path / filename))
                                
                    except Exception as e:
                        print(f"Error procesando imagen: {e}")
                        continue
                        
        finally:
            driver.quit()
            
        return downloaded_images

# Ejemplo de uso
if __name__ == "__main__":
    scraper = ImageScraper()
    
    # Scrapear imágenes de Puma
    puma_images = scraper.scrape_images('puma', limit=30)
    print(f"Se descargaron {len(puma_images)} imágenes de Puma")