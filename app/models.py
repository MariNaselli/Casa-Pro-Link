from . import db

class Propiedad(db.Model):
    # Control Interno
    id = db.Column(db.Integer, primary_key=True)
    
    # Comercial (Público)
    titulo = db.Column(db.String(100), nullable=False)
    operacion = db.Column(db.String(20))
    precio = db.Column(db.Integer)
    moneda = db.Column(db.String(10), default='ARS')
    expensas = db.Column(db.Integer)
    calle = db.Column(db.String(200))  
    altura = db.Column(db.String(50))
    barrio = db.Column(db.String(100)) 
    descripcion = db.Column(db.Text)
    archivos = db.relationship('Multimedia', backref='propiedad', lazy=True)
    
    # Ficha Técnica
    m2_totales = db.Column(db.Integer)
    m2_cubiertos = db.Column(db.Integer)
    dormitorios = db.Column(db.Integer)
    banios = db.Column(db.Integer)
    
    # Datos Privados
    propietario_nombre = db.Column(db.String(100))
    propietario_tel = db.Column(db.String(50))
    notas_internas = db.Column(db.Text)
    
    activo = db.Column(db.Boolean, default=True)
    
class Multimedia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False) # Guardaremos 'imagen' o 'video'
    propiedad_id = db.Column(db.Integer, db.ForeignKey('propiedad.id'), nullable=False)