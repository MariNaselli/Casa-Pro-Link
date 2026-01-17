from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 1. Inicializamos la base de datos sin conectarla aún
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configuraciones
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casaprolink.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = 'tu_llave_secreta_aqui'

    # 2. Conectamos la base de datos con la app
    db.init_app(app)

    # 3. Registramos las rutas
    with app.app_context():
        from . import routes
        # Si usaste Blueprints esto cambia, pero si es simple, con el import alcanza
        
    return app