from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    # PERMITIR SUBIR ARCHIVOS (VIDEOS/IMÁGENES) DE HASTA 100 MB
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
    
    db.init_app(app)
    
    # Configuramos el LoginManager
    login_manager.init_app(app)
    login_manager.login_view = 'login' # Si alguien intenta entrar a algo prohibido, lo manda acá
    login_manager.login_message = "Por favor, inicia sesión para acceder."
    login_manager.login_message_category = "warning"

    with app.app_context():
        from . import routes
        from .models import Usuario # Importamos el modelo para el loader

        # Función necesaria para que Flask-Login encuentre al usuario en la BD
        @login_manager.user_loader
        def load_user(user_id):
            return Usuario.query.get(int(user_id))

    return app
