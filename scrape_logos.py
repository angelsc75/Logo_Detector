from icrawler.builtin import GoogleImageCrawler
import os

def scrape_logos(search_term, num_images, output_dir):
    """
    Descarga imágenes de Google usando icrawler
    
    Args:
        search_term: término de búsqueda (ej: "adidas logo")
        num_images: número de imágenes a descargar
        output_dir: directorio donde guardar las imágenes
    """
    # Crear el directorio si no existe
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Configurar el crawler
    google_crawler = GoogleImageCrawler(
        storage={'root_dir': output_dir},
        feeder_threads=1,
        parser_threads=1,
        downloader_threads=4
    )
    
    # Configurar los filtros de búsqueda
    filters = {
        'size': 'medium',
        'license': 'commercial,modify',
        'type': 'photo'
    }
    
    print(f"Descargando {num_images} imágenes de '{search_term}'...")
    
    # Realizar la búsqueda y descarga
    google_crawler.crawl(
        keyword=search_term,
        max_num=num_images,
        filters=filters,
        file_idx_offset=0
    )
    
    print(f"Descarga completada en {output_dir}")

# Ejemplo de uso
if __name__ == "__main__":
    # Directorio base para el dataset
    base_dir = "dataset"
    
    # Descargar logos de Adidas
    scrape_logos(
        search_term="adidas logo",
        num_images=100,
        output_dir=os.path.join(base_dir, "images", "adidas")
    )
    
    # Descargar logos de Nike
    scrape_logos(
        search_term="nike logo",
        num_images=100,
        output_dir=os.path.join(base_dir, "images", "nike")
    )