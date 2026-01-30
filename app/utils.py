import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

def guardar_archivo_multimedia(file, tipo_folder='uploads', optimizar=False):
    """
    Procesa fotos, videos y documentos.
    Crea la carpeta si no existe y optimiza imágenes si se solicita.
    """
    if not file or file.filename == '':
        return None
    
    # 1. Limpiamos el nombre original y creamos uno único
    filename = secure_filename(file.filename)
    nombre_unico = f"{uuid.uuid4().hex}_{filename}"
    
    # 2. Definimos la ruta de la carpeta (uploads o documentos)
    # Usamos la variable tipo_folder que viene por parámetro
    folder_path = os.path.join(current_app.static_folder, tipo_folder)
    
    # 3. SEGURIDAD: Si la carpeta no existe, la creamos
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # 4. Ruta final completa del archivo
    ruta_final = os.path.join(folder_path, nombre_unico)
    file.save(ruta_final)

    # 5. Optimización de imágenes (solo si es imagen y se pide optimizar)
    if optimizar:
        extension = nombre_unico.lower().split('.')[-1]
        if extension in ['jpg', 'jpeg', 'png', 'webp']:
            try:
                with Image.open(ruta_final) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Redimensionamos a un tamaño máximo razonable (Full HD aprox)
                    img.thumbnail((1600, 1600)) 
                    
                    # Guardamos comprimiendo para que la web vuele
                    img.save(ruta_final, "JPEG", optimize=True, quality=80)
            except Exception as e:
                print(f"Error optimizando imagen: {e}")
                
    return nombre_unico

import re
import unicodedata

def generar_slug(texto):
    # Pasa a minúsculas y normaliza acentos
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('utf-8').lower()
    # Quita caracteres que no sean letras o números y reemplaza espacios por guiones
    slug = re.sub(r'[^a-z0-9]+', '-', texto).strip('-')
    return slug