import cv2
import os
import xml.etree.ElementTree as ET
from pathlib import Path

class ManualLabeler:
    def __init__(self, images_dir):
        self.images_dir = Path(images_dir)
        
        # Verificar que el directorio existe
        if not self.images_dir.exists():
            raise Exception(f"El directorio de imágenes no existe: {self.images_dir}")
            
        self.annotations_dir = self.images_dir.parent / 'annotations'
        self.annotations_dir.mkdir(exist_ok=True)
        
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.current_bbox = []
        self.image = None
        self.original_image = None
        self.current_brand = None
        self.window_name = 'Manual Labeler'
    
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y
            self.current_bbox = []
        
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.image = self.original_image.copy()
                cv2.rectangle(self.image, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            x1, x2 = min(self.ix, x), max(self.ix, x)
            y1, y2 = min(self.iy, y), max(self.iy, y)
            self.current_bbox = [x1, y1, x2, y2]
            cv2.rectangle(self.image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    def create_xml_annotation(self, image_path, bbox):
        """Crea un archivo XML con el mismo formato que Logos in the Wild"""
        height, width = self.original_image.shape[:2]
        
        # Crear el elemento raíz annotation
        annotation = ET.Element('annotation')
        
        # Añadir folder
        folder = ET.SubElement(annotation, 'folder')
        folder.text = str(self.images_dir.name)
        
        # Añadir filename
        filename = ET.SubElement(annotation, 'filename')
        filename.text = str(image_path.name)
        
        # Añadir path
        path = ET.SubElement(annotation, 'path')
        path.text = str(image_path)
        
        # Añadir source
        source = ET.SubElement(annotation, 'source')
        database = ET.SubElement(source, 'database')
        database.text = 'Unknown'
        
        # Añadir size
        size = ET.SubElement(annotation, 'size')
        width_elem = ET.SubElement(size, 'width')
        width_elem.text = str(width)
        height_elem = ET.SubElement(size, 'height')
        height_elem.text = str(height)
        depth_elem = ET.SubElement(size, 'depth')
        depth_elem.text = '3'
        
        # Añadir segmented
        segmented = ET.SubElement(annotation, 'segmented')
        segmented.text = '0'
        
        # Añadir object
        obj = ET.SubElement(annotation, 'object')
        
        # Nombre del objeto (marca)
        name = ET.SubElement(obj, 'name')
        name.text = self.current_brand
        
        # Pose
        pose = ET.SubElement(obj, 'pose')
        pose.text = 'Unspecified'
        
        # Truncated
        truncated = ET.SubElement(obj, 'truncated')
        truncated.text = '0'
        
        # Difficult
        difficult = ET.SubElement(obj, 'difficult')
        difficult.text = '0'
        
        # Bounding box
        bndbox = ET.SubElement(obj, 'bndbox')
        xmin = ET.SubElement(bndbox, 'xmin')
        xmin.text = str(bbox[0])
        ymin = ET.SubElement(bndbox, 'ymin')
        ymin.text = str(bbox[1])
        xmax = ET.SubElement(bndbox, 'xmax')
        xmax.text = str(bbox[2])
        ymax = ET.SubElement(bndbox, 'ymax')
        ymax.text = str(bbox[3])
        
        # Crear el árbol XML y guardarlo
        tree = ET.ElementTree(annotation)
        xml_path = self.annotations_dir / f"{image_path.stem}.xml"
        
        # Escribir el archivo con la declaración XML y la codificación correcta
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            tree.write(f, encoding='unicode', method='xml')
        
        print(f"Anotación guardada en: {xml_path}")
        
    def label_images(self):
        # Obtener lista de imágenes
        image_files = list(self.images_dir.glob('*.jpg')) + list(self.images_dir.glob('*.png'))
        
        print(f"Buscando imágenes en: {self.images_dir}")
        print(f"Encontradas {len(image_files)} imágenes")
        
        if not image_files:
            print("No se encontraron imágenes .jpg o .png en el directorio")
            return
            
        # Configurar la ventana y el callback del mouse
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\nControles:")
        print("- Arrastrar con el botón izquierdo para dibujar el bounding box")
        print("- Presionar 'a' para etiquetar como Adidas")
        print("- Presionar 'p' para etiquetar como Puma")
        print("- Presionar 'r' para resetear el bounding box actual")
        print("- Presionar 'q' para salir")
        print("- Presionar cualquier otra tecla para pasar a la siguiente imagen sin etiquetar\n")
        
        for img_path in image_files:
            print(f"Abriendo: {img_path}")
            self.original_image = cv2.imread(str(img_path))
            
            if self.original_image is None:
                print(f"No se pudo cargar la imagen: {img_path}")
                continue
                
            print(f"Imagen cargada: {img_path}")
            self.image = self.original_image.copy()
            self.current_bbox = []
            
            while True:
                cv2.imshow(self.window_name, self.image)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("Cerrando el programa...")
                    cv2.destroyAllWindows()
                    return
                
                elif key == ord('r'):
                    self.image = self.original_image.copy()
                    self.current_bbox = []
                    print("Bounding box reseteado")
                
                elif key == ord('a') and self.current_bbox:
                    self.current_brand = 'adidas'
                    self.create_xml_annotation(img_path, self.current_bbox)
                    print(f"Guardada anotación para {img_path.name} como Adidas")
                    break
                    
                elif key == ord('p') and self.current_bbox:
                    self.current_brand = 'puma'
                    self.create_xml_annotation(img_path, self.current_bbox)
                    print(f"Guardada anotación para {img_path.name} como Puma")
                    break
                
                elif key != 255:
                    if self.current_bbox:
                        print("Por favor, selecciona una marca (a/p) antes de continuar")
                    else:
                        print("Saltando imagen sin anotación")
                        break
        
        cv2.destroyAllWindows()

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Asegúrate de poner aquí la ruta correcta a tu carpeta de imágenes
        images_path = "dataset/images"
        print(f"Iniciando etiquetador con directorio: {images_path}")
        labeler = ManualLabeler(images_path)
        labeler.label_images()
    except Exception as e:
        print(f"Error: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Asegúrate de poner aquí la ruta correcta a tu carpeta de imágenes
        images_path = "dataset/images/puma"
        print(f"Iniciando etiquetador con directorio: {images_path}")
        labeler = ManualLabeler(images_path)
        labeler.label_images()
    except Exception as e:
        print(f"Error: {e}")