from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Propiedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    operacion = db.Column(db.String(20))
    precio = db.Column(db.Integer)
    moneda = db.Column(db.String(10), default='ARS')
    expensas = db.Column(db.Integer)
    calle = db.Column(db.String(200))
    altura = db.Column(db.String(50))
    barrio = db.Column(db.String(100))
    descripcion = db.Column(db.Text)
    m2_totales = db.Column(db.Integer)
    m2_cubiertos = db.Column(db.Integer)
    dormitorios = db.Column(db.Integer)
    banios = db.Column(db.Integer)
    notas_internas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    mostrar_inmo = db.Column(db.Boolean, default=False)
    
    # --- COMODIDADES ---
    cochera = db.Column(db.Boolean, default=False)
    pileta = db.Column(db.Boolean, default=False)
    quincho = db.Column(db.Boolean, default=False)
    patio = db.Column(db.Boolean, default=False)
    
    # RELACIONES (Una sola vez cada una)
    archivos = db.relationship('Multimedia', backref='propiedad', lazy=True)
    propietarios = db.relationship('Propietario', backref='propiedad', lazy=True)

class Propietario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))
    dni = db.Column(db.String(20))
    domicilio_particular = db.Column(db.String(200))
    notas_legajo = db.Column(db.Text) # Aquí podés anotar datos de la escritura
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedad.id'), nullable=False)

class Multimedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedad.id'), nullable=False)

class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
