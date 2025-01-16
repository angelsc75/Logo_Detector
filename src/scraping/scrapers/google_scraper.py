from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from .scraper_base import ImageScraperBase

class GoogleImageScraper(ImageScraperBase):
    def __init__(self, save_dir: str):
        super().__init__(save_dir)
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--headless')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    def scrape(self, brand: str, limit: int = 30):
        """Realiza el scraping de imágenes de Google Images."""
        downloaded_images = []
        driver = None
        
        try:
            driver = webdriver.Chrome(options=self.options)
            search_queries = [
                f"{brand} logo transparent",
                f"{brand} official logo",
                f"{brand} brand logo"
            ]
            
            for query in search_queries:
                if len(downloaded_images) >= limit:
                    break
                    
                self.logger.info(f"Buscando: {query}")
                search_url = f"https://www.google.com/search?q={query}&tbm=isch"
                driver.get(search_url)
                
                try:
                    # Esperar a que las imágenes carguen
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "img.rg_i"))
                    )
                    
                    # Scroll para cargar más imágenes
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    while len(downloaded_images) < limit:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                    
                    # Encontrar y procesar imágenes
                    images = driver.find_elements(By.CSS_SELECTOR, "img.rg_i")
                    
                    for idx, img in enumerate(images):
                        if len(downloaded_images) >= limit:
                            break
                            
                        try:
                            img.click()
                            time.sleep(1)
                            
                            actual_image = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "img.r48jcc"))
                            )
                            
                            img_url = actual_image.get_attribute("src")
                            if img_url and img_url.startswith("http"):
                                filename = f"{brand}_logo_{len(downloaded_images)}.jpg"
                                if self.save_image(img_url, filename, brand):
                                    downloaded_images.append(filename)
                                    
                        except TimeoutException:
                            continue
                        except Exception as e:
                            self.logger.error(f"Error procesando imagen: {str(e)}")
                            continue
                            
                except Exception as e:
                    self.logger.error(f"Error en la búsqueda {query}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error general en el scraping: {str(e)}")
        finally:
            if driver:
                driver.quit()
                
        self.logger.info(f"Total de imágenes descargadas para {brand}: {len(downloaded_images)}")
        return downloaded_images
te