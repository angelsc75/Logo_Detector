import os
import xml.etree.ElementTree as ET
from pathlib import Path
import shutil

def convert_xml_to_yolo(xml_path, image_width, image_height):
    """
    Convierte las coordenadas de formato XML a formato YOLO
    YOLO format: <class> <x_center> <y_center> <width> <height>
    Valores normalizados entre 0 y 1
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    yolo_annotations = []
    
    for obj in root.findall('.//object'):
        # Obtener el nombre de la clase
        class_name = obj.find('name').text.lower()
        
        # Mapear nombres de clase a índices
        class_mapping = {'adidas': 0, 'puma': 1}
        
        # Solo procesar si la clase está en nuestro mapping
        if class_name not in class_mapping:
            continue
            
        class_idx = class_mapping[class_name]
        
        # Obtener el bounding box
        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        ymin = float(bbox.find('ymin').text)
        xmax = float(bbox.find('xmax').text)
        ymax = float(bbox.find('ymax').text)
        
        # Convertir a formato YOLO (normalizado)
        x_center = ((xmin + xmax) / 2) / image_width
        y_center = ((ymin + ymax) / 2) / image_height
        width = (xmax - xmin) / image_width
        height = (ymax - ymin) / image_height
        
        # Asegurarse de que los valores estén entre 0 y 1
        x_center = min(max(x_center, 0.0), 1.0)
        y_center = min(max(y_center, 0.0), 1.0)
        width = min(max(width, 0.0), 1.0)
        height = min(max(height, 0.0), 1.0)
        
        yolo_annotations.append(f"{class_idx} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    return yolo_annotations

def get_image_dimensions(xml_path):
    """Obtiene las dimensiones de la imagen del archivo XML"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    size = root.find('size')
    if size is not None:
        width = float(size.find('width').text)
        height = float(size.find('height').text)
        return width, height
    return None, None

def process_dataset(input_path, output_path):
    """
    Procesa todo el dataset convirtiendo anotaciones XML a formato YOLO
    y organizando los archivos en la estructura requerida por YOLOv8
    """
    # Crear directorios de salida
    os.makedirs(output_path, exist_ok=True)
    
    # Crear archivo data.yaml
    yaml_content = """
path: {dataset_path}
train: train/images
val: valid/images
test: test/images

nc: 2
names: ['adidas', 'puma']
    """.format(dataset_path=output_path)
    
    with open(os.path.join(output_path, 'data.yaml'), 'w') as f:
        f.write(yaml_content.strip())
    
    # Procesar cada split (train, valid, test)
    for split in ['train', 'valid', 'test']:
        # Crear directorios para el split actual
        split_img_dir = os.path.join(output_path, split, 'images')
        split_label_dir = os.path.join(output_path, split, 'labels')
        os.makedirs(split_img_dir, exist_ok=True)
        os.makedirs(split_label_dir, exist_ok=True)
        
        # Directorios de entrada
        input_images_dir = os.path.join(input_path, split, 'images')
        input_labels_dir = os.path.join(input_path, split, 'labels')
        
        # Procesar cada imagen en el split
        for img_file in os.listdir(input_images_dir):
            if img_file.endswith(('.jpg', '.jpeg', '.png')):
                # Copiar imagen
                src_img = os.path.join(input_images_dir, img_file)
                dst_img = os.path.join(split_img_dir, img_file)
                shutil.copy2(src_img, dst_img)
                
                # Procesar anotación si existe
                base_name = os.path.splitext(img_file)[0]
                xml_file = os.path.join(input_labels_dir, f"{base_name}.xml")
                
                if os.path.exists(xml_file):
                    try:
                        # Obtener dimensiones de la imagen
                        width, height = get_image_dimensions(xml_file)
                        if width is None or height is None:
                            print(f"Warning: No se pudieron obtener dimensiones para {img_file}")
                            continue
                        
                        # Convertir anotaciones
                        yolo_annotations = convert_xml_to_yolo(xml_file, width, height)
                        
                        # Guardar anotaciones en formato YOLO
                        txt_file = os.path.join(split_label_dir, f"{base_name}.txt")
                        with open(txt_file, 'w') as f:
                            f.write('\n'.join(yolo_annotations))
                    except Exception as e:
                        print(f"Error procesando {xml_file}: {str(e)}")
                else:
                    # Crear archivo vacío para imágenes sin anotaciones (background)
                    txt_file = os.path.join(split_label_dir, f"{base_name}.txt")
                    with open(txt_file, 'w') as f:
                        f.write("")

if __name__ == "__main__":
    # Rutas de entrada y salida
    input_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\brand_detection_Angel_Leire\data\dataset_ok"
    output_path = r"C:\Users\ang01\Desktop\CURSO F5\25 Proyecto de Computer Vision\brand_detection_Angel_Leire\data\dataset_yolo"
    
    # Procesar el dataset
    process_dataset(input_path, output_path)
    print("Conversión completada!")