import os

# Determinamos la ruta de la carpeta 'instance'
# Esto busca la carpeta donde está parado este archivo y le suma 'instance'
basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, 'instance')

class Config:
    SECRET_KEY = 'admin-secret'
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///casaprolink.db' <-- ESTA ERA LA VIEJA
    
    # ESTA ES LA NUEVA (Apunta a instance/casaprolink.db de forma segura)
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(instance_path, "casaprolink.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False