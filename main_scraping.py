
from src.scraping.scraper import ImageScraper
import logging

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    try:
        # Crear el scraper
        scraper = ImageScraper()
        
        # Lista de marcas a scrapear
        brands = ['puma', 'adidas']
        
        for brand in brands:
            logging.info(f"Iniciando scraping de {brand}")
            images = scraper.scrape_images(brand, limit=30)
            logging.info(f"Se descargaron {len(images)} imágenes de {brand}")
            
    except Exception as e:
        logging.error(f"Error durante el scraping: {e}")
        
if __name__ == "__main__":
    main()