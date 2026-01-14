from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# Configuración: le decimos dónde guardar el archivo de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///casaprolink.db'
db = SQLAlchemy(app)

# Definimos cómo es una "Propiedad" en nuestra base de datos
class Propiedad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100))
    precio = db.Column(db.Integer)

# Creamos la base de datos físicamente
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/cargar')
def cargar():
    return render_template('cargar.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    # Capturamos lo que el usuario escribió en los inputs
    titulo_recibido = request.form.get('titulo')
    precio_recibido = request.form.get('precio')
    
    # 2. Creamos un nuevo objeto "Propiedad" con esos datos
    nueva_propiedad = Propiedad(titulo=titulo_recibido, precio=precio_recibido)
    
    # 3. Lo guardamos en la base de datos
    db.session.add(nueva_propiedad)
    db.session.commit()
    
    # Por ahora, solo lo mostramos en pantalla para ver que funciona
    return f"<h1>¡Guardado con éxito!</h1><p>La propiedad '{titulo_recibido}' ya está en la base de datos.</p><a href='/cargar'>Cargar otra</a>"

if __name__ == '__main__':
    app.run(debug=True)