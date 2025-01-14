import os
import shutil
import random
from pathlib import Path
import xml.etree.ElementTree as ET

def organize_dataset(source_path, output_path, train_ratio=0.7, valid_ratio=0.2):
    # Crear directorios de destino
    for split in ['train', 'valid', 'test']:
        os.makedirs(f"{output_path}/{split}/images", exist_ok=True)
        os.makedirs(f"{output_path}/{split}/labels", exist_ok=True)

    # Marcas que nos interesan
    target_brands = ['adidas', 'puma', 'background']
    all_images = []

    # Recopilar todas las imágenes de las marcas objetivo
    for brand in target_brands:
        brand_path = Path(source_path) / brand
        if brand_path.exists():
            # Obtener todas las imágenes y sus anotaciones XML
            image_files = list(brand_path.glob('*.jpg'))
            for img_path in image_files:
                # Buscar el archivo XML correspondiente
                xml_path = img_path.with_suffix('.xml')
                if xml_path.exists():
                    try:
                        # Verificar que el XML contiene anotaciones válidas
                        tree = ET.parse(xml_path)
                        root = tree.getroot()
                        if root.findall('.//object'):  # Verifica si hay objetos anotados
                            all_images.append((img_path, xml_path, brand))
                    except ET.ParseError:
                        print(f"Error al parsear {xml_path}")
                        continue
            
            print(f"Encontradas {len(image_files)} imágenes para {brand}")
            print(f"De las cuales {len([x for x in all_images if x[2] == brand])} tienen anotaciones XML válidas")

    # Mezclar aleatoriamente todas las imágenes
    random.shuffle(all_images)

    # Calcular índices para la división
    n = len(all_images)
    train_idx = int(n * train_ratio)
    valid_idx = int(n * (train_ratio + valid_ratio))

    # Función para copiar imágenes y anotaciones
    def copy_files(images_subset, split):
        for img_path, xml_path, brand in images_subset:
            # Copiar imagen
            dest_img = Path(output_path) / split / 'images' / img_path.name
            shutil.copy(str(img_path), str(dest_img))
            
            # Copiar anotación XML
            dest_xml = Path(output_path) / split / 'labels' / xml_path.name
            shutil.copy(str(xml_path), str(dest_xml))

    # Dividir y copiar archivos
    copy_files(all_images[:train_idx], 'train')
    copy_files(all_images[train_idx:valid_idx], 'valid')
    copy_files(all_images[valid_idx:], 'test')

    # Imprimir estadísticas finales
    print("\nDistribución final del dataset:")
    print(f"Train: {train_idx} imágenes")
    print(f"Validation: {valid_idx - train_idx} imágenes")
    print(f"Test: {n - valid_idx} imágenes")
    print(f"Total: {n} imágenes")

    # Imprimir distribución por marca
    for brand in target_brands:
        brand_count = len([x for x in all_images if x[2] == brand])
        print(f"\nTotal {brand}: {brand_count} imágenes")
        print(f"Train {brand}: {len([x for x in all_images[:train_idx] if x[2] == brand])}")
        print(f"Valid {brand}: {len([x for x in all_images[train_idx:valid_idx] if x[2] == brand])}")
        print(f"Test {brand}: {len([x for x in all_images[valid_idx:] if x[2] == brand])}")

# Rutas
source_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\brand_detection_Angel_Leire\dataset_final"
output_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\brand_detection_Angel_Leire\dataset"

# Ejecutar la organización del dataset
organize_dataset(source_path, output_path)