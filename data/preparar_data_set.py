import os
import shutil
from sklearn.model_selection import train_test_split
import glob
import xml.etree.ElementTree as ET

def read_xml_annotation(xml_path):
    """
    Lee un archivo XML de anotación y extrae las marcas presentes
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    brands = []
    
    # Buscar todos los objetos en la anotación
    for obj in root.findall('.//object'):
        name = obj.find('name').text.lower()
        if name in ['adidas', 'puma', 'nike']:  # Añadido nike
            # Obtener coordenadas del bounding box
            bbox = obj.find('bndbox')
            xmin = float(bbox.find('xmin').text)
            ymin = float(bbox.find('ymin').text)
            xmax = float(bbox.find('xmax').text)
            ymax = float(bbox.find('ymax').text)
            
            # Convertir a formato YOLO (x_center, y_center, width, height)
            img_width = float(root.find('.//width').text)
            img_height = float(root.find('.//height').text)
            
            x_center = (xmin + xmax) / (2.0 * img_width)
            y_center = (ymin + ymax) / (2.0 * img_height)
            width = (xmax - xmin) / img_width
            height = (ymax - ymin) / img_height
            
            brands.append({
                'name': name,
                'bbox': [x_center, y_center, width, height]
            })
    
    return brands

def prepare_yolo_dataset(
    qmul_path,
    output_path,
    train_size=0.7,
    val_size=0.15,
    test_size=0.15
):
    """
    Prepara un dataset para YOLO a partir de QMUL-OpenLogo
    """
    print(f"Iniciando preparación del dataset...")
    
    # Verificar directorios de entrada
    images_dir = os.path.join(qmul_path, 'JPEGImages')
    annotations_dir = os.path.join(qmul_path, 'Annotations')
    
    if not all(os.path.exists(d) for d in [images_dir, annotations_dir]):
        print("Error: No se encuentran los directorios necesarios")
        return
    
    # Crear estructura de directorios de salida
    splits = ['train', 'val', 'test']
    for split in splits:
        os.makedirs(os.path.join(output_path, split, 'images'), exist_ok=True)
        os.makedirs(os.path.join(output_path, split, 'labels'), exist_ok=True)
    print("Directorios creados correctamente")

    # Mapeo de clases
    class_map = {
        'adidas': 0,
        'puma': 1,
        'nike': 2  # Añadido nike
    }

    # Recolectar imágenes y anotaciones relevantes
    relevant_files = []
    print("Analizando anotaciones...")
    
    # Listar todos los archivos XML
    xml_files = glob.glob(os.path.join(annotations_dir, '*.xml'))
    total_processed = 0
    brand_counts = {'adidas': 0, 'puma': 0, 'nike': 0}
    
    for xml_path in xml_files:
        base_name = os.path.splitext(os.path.basename(xml_path))[0]
        img_path = os.path.join(images_dir, f"{base_name}.jpg")
        
        if not os.path.exists(img_path):
            continue
            
        brands = read_xml_annotation(xml_path)
        if brands:  # Si encontramos alguno de los logos
            relevant_files.append((img_path, xml_path, brands))
            # Contar logos por marca
            for brand in brands:
                brand_counts[brand['name']] += 1
        
        total_processed += 1
        if total_processed % 100 == 0:
            print(f"Procesados {total_processed} archivos...")
    
    print(f"\nEncontrados {len(relevant_files)} archivos con logos relevantes")
    print("Distribución de logos:")
    for brand, count in brand_counts.items():
        print(f"- {brand.capitalize()}: {count} logos")
    
    # Dividir en train/val/test
    train_files, temp_files = train_test_split(relevant_files, train_size=train_size, random_state=42)
    val_files, test_files = train_test_split(temp_files, train_size=val_size/(val_size + test_size), random_state=42)
    
    # Procesar cada split
    for files, split_name in zip([train_files, val_files, test_files], splits):
        print(f"\nProcesando split {split_name} ({len(files)} archivos)")
        
        for img_path, xml_path, brands in files:
            # Copiar imagen
            shutil.copy2(img_path, os.path.join(output_path, split_name, 'images'))
            
            # Crear archivo de etiquetas YOLO
            base_name = os.path.splitext(os.path.basename(img_path))[0]
            label_path = os.path.join(output_path, split_name, 'labels', f"{base_name}.txt")
            
            with open(label_path, 'w') as f:
                for brand in brands:
                    class_id = class_map[brand['name']]
                    bbox = brand['bbox']
                    f.write(f"{class_id} {' '.join(map(str, bbox))}\n")
    
    # Crear archivo data.yaml
    yaml_content = f"""
train: {os.path.join(output_path, 'train')}
val: {os.path.join(output_path, 'val')}
test: {os.path.join(output_path, 'test')}

nc: {len(class_map)}
names: {list(class_map.keys())}
    """
    
    with open(os.path.join(output_path, 'data.yaml'), 'w') as f:
        f.write(yaml_content)
        
    print(f"\nDataset preparado exitosamente en: {output_path}")
    print("\nResumen final:")
    print(f"- Train: {len(train_files)} imágenes")
    print(f"- Validación: {len(val_files)} imágenes")
    print(f"- Test: {len(test_files)} imágenes")

if __name__ == "__main__":
    qmul_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\openlogo"
    output_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\brand_detection_Angel_Leire\data\dataset_yolo"

    prepare_yolo_dataset(
        qmul_path=qmul_path,
        output_path=output_path
    )