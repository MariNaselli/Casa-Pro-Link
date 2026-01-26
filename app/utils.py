import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

def guardar_archivo_multimedia(file, tipo_folder='uploads', optimizar=False):
    """
    Lógica única para procesar cualquier archivo.
    Devuelve el nombre único del archivo guardado.
    """
    if not file or file.filename == '':
        return None
    
    filename = secure_filename(file.filename)
    # Agregamos prefijo DOC para legajos si queremos orden visual en la carpeta
    prefix = "DOC_" if tipo_folder == 'documentos' else "" 
    nombre_unico = f"{prefix}{uuid.uuid4().hex}_{filename}"
    
    ruta = os.path.join(current_app.static_folder, 'uploads', nombre_unico)
    file.save(ruta)

    if optimizar:
        extension = nombre_unico.lower().split('.')[-1]
        if extension in ['jpg', 'jpeg', 'png']:
            try:
                with Image.open(ruta) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.thumbnail((1200, 1200)) # Redimensiona manteniendo proporción
                    img.save(ruta, "JPEG", optimize=True, quality=75)
            except Exception as e:
                print(f"Error optimizando {nombre_unico}: {e}")
                
    return nombre_unico