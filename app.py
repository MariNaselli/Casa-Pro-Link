from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configuración: le decimos dónde guardar el archivo de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casaprolink.db'
db = SQLAlchemy(app)

class Propiedad(db.Model):
    # Control Interno
    id = db.Column(db.Integer, primary_key=True)
    
    # Comercial (Público)
    titulo = db.Column(db.String(100), nullable=False)
    operacion = db.Column(db.String(20))  # Venta o Alquiler
    precio = db.Column(db.Integer)
    expensas = db.Column(db.Integer)
    ubicacion = db.Column(db.String(200))
    descripcion = db.Column(db.Text)
    
    # Ficha Técnica
    m2_totales = db.Column(db.Integer)
    m2_cubiertos = db.Column(db.Integer)
    dormitorios = db.Column(db.Integer)
    banios = db.Column(db.Integer)
    
    # Datos Privados
    propietario_nombre = db.Column(db.String(100))
    propietario_tel = db.Column(db.String(50))
    notas_internas = db.Column(db.Text)

# Creamos la base de datos físicamente
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    # Obtenemos lo que el usuario escribió
    query = request.args.get('q', '') # El '' es para que no sea None si está vacío
    
    # Si hay algo escrito (quitando espacios en blanco con strip)
    if query.strip():
        lista_propiedades = Propiedad.query.filter(
            (Propiedad.titulo.contains(query)) | 
            (Propiedad.ubicacion.contains(query))
        ).all()
    else:
        # Si el buscador está vacío, traemos absolutamente todo
        lista_propiedades = Propiedad.query.all()
        
    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar')
def cargar():
    return render_template('cargar.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    # Capturamos lo que el usuario escribió en los inputs
    titulo_recibido = request.form.get('titulo')
    precio_recibido = request.form.get('precio')
    ubicacion_recibida = request.form.get('ubicacion')
    propietario_recibido = request.form.get('propietario')
    
    # 2. Creamos un nuevo objeto "Propiedad" con esos datos
    nueva_propiedad = Propiedad(
        titulo=titulo_recibido, 
        precio=precio_recibido,
        ubicacion=ubicacion_recibida,
        propietario_nombre=propietario_recibido
        )
    
    # 3. Lo guardamos en la base de datos
    db.session.add(nueva_propiedad)
    db.session.commit()
    
    # Por ahora, solo lo mostramos en pantalla para ver que funciona
    return f"<h1>¡Guardado!</h1><p>Propiedad: {titulo_recibido} en {ubicacion_recibida} cargada correctamente.</p><a href='/cargar'>Cargar otra</a>"

if __name__ == '__main__':
    app.run(debug=True)