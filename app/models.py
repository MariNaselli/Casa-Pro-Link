from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class TipoPropiedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    propiedades = db.relationship('Propiedad', backref='tipo', lazy=True)

class TipoOperacion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False)
    propiedades = db.relationship('Propiedad', backref='operacion_rel', lazy=True)

class Barrio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    propiedades = db.relationship('Propiedad', backref='barrio_rel', lazy=True)

class Propiedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    slug = db.Column(db.String(255), unique=True, nullable=True)
    
    tipo_id = db.Column(db.Integer, db.ForeignKey('tipo_propiedad.id'))
    operacion_id = db.Column(db.Integer, db.ForeignKey('tipo_operacion.id'))
    barrio_id = db.Column(db.Integer, db.ForeignKey('barrio.id'))
    
    localidad = db.Column(db.String(100), default='Córdoba')
    calle = db.Column(db.String(200))
    altura = db.Column(db.String(50))
    codigo_postal = db.Column(db.String(20))

    # --- NUEVOS CAMPOS PARA EL MAPA ---
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    # ----------------------------------
    
    precio = db.Column(db.Integer)
    moneda = db.Column(db.String(10), default='ARS')
    expensas = db.Column(db.Integer)
    m2_totales = db.Column(db.Integer)
    m2_cubiertos = db.Column(db.Integer)
    dormitorios = db.Column(db.Integer, default=0)
    banios = db.Column(db.Integer, default=0)
    
    estado = db.Column(db.String(20), default='Disponible')
    destacada = db.Column(db.Boolean, default=False)
    activo = db.Column(db.Boolean, default=True)
    fecha_carga = db.Column(db.DateTime, default=datetime.utcnow)
    
    notas_internas = db.Column(db.Text)
    mostrar_inmo = db.Column(db.Boolean, default=False)
    cochera = db.Column(db.Boolean, default=False)
    pileta = db.Column(db.Boolean, default=False)
    quincho = db.Column(db.Boolean, default=False)
    patio = db.Column(db.Boolean, default=False)
    terraza = db.Column(db.Boolean, default=False)
    balcon = db.Column(db.Boolean, default=False)
    
    archivos = db.relationship('Multimedia', backref='propiedad', lazy=True, cascade="all, delete-orphan")
    propietarios = db.relationship('Propietario', backref='propiedad', lazy=True)

class Propietario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    telefono = db.Column(db.String(50))
    email = db.Column(db.String(100))
    dni = db.Column(db.String(20))
    notas_legajo = db.Column(db.Text)
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