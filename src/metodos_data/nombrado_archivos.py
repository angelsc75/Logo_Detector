import os
import shutil
from pathlib import Path

def rename_logo_files(images_dir, annotations_dir, output_dir, prefix='logo'):
    """
    Renombra archivos de imágenes y sus correspondientes archivos XML de anotaciones
    con el mismo nombre base y los coloca en el directorio de salida.
    
    Args:
        images_dir (str): Directorio que contiene las imágenes
        annotations_dir (str): Directorio que contiene los archivos XML
        output_dir (str): Directorio donde se guardarán los archivos renombrados
        prefix (str): Prefijo para los nuevos nombres de archivo
    """
    # Crear el directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtener lista de imágenes
    image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    xml_files = [f for f in os.listdir(annotations_dir) if f.lower().endswith('.xml')]
    
    # Verificar que hay el mismo número de imágenes y archivos XML
    if len(image_files) != len(xml_files):
        print(f"¡Advertencia! Número diferente de imágenes ({len(image_files)}) y archivos XML ({len(xml_files)})")
    
    # Renombrar y mover archivos
    for idx, (img_file, xml_file) in enumerate(zip(sorted(image_files), sorted(xml_files))):
        # Generar nuevos nombres
        new_name = f"{prefix}_{str(idx+1).zfill(4)}"
        
        # Obtener extensión original de la imagen
        img_ext = Path(img_file).suffix
        
        # Rutas completas para los nuevos archivos
        new_img_path = os.path.join(output_dir, f"{new_name}{img_ext}")
        new_xml_path = os.path.join(output_dir, f"{new_name}.xml")
        
        # Copiar y renombrar archivos
        shutil.copy2(
            os.path.join(images_dir, img_file),
            new_img_path
        )
        shutil.copy2(
            os.path.join(annotations_dir, xml_file),
            new_xml_path
        )
        
        print(f"Procesado {idx+1}: {img_file} → {new_name}{img_ext}")

# Ejemplo de uso
if __name__ == "__main__":
    # Definir directorios (ajusta estas rutas según tu estructura)
    IMAGES_DIR = "./dataset/images/background"
    ANNOTATIONS_DIR = "./dataset/images/background"
    OUTPUT_DIR = "./dataset_final/background"
    
    rename_logo_files(
        images_dir=IMAGES_DIR,
        annotations_dir=ANNOTATIONS_DIR,
        output_dir=OUTPUT_DIR,
        prefix='background'  # puedes cambiar el prefijo según necesites
    )