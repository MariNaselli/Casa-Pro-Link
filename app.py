from flask import Flask, render_template, request

app = Flask(__name__)

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
    
    # Por ahora, solo lo mostramos en pantalla para ver que funciona
    return f"<h1>¡Datos recibidos!</h1><p>Propiedad: {titulo_recibido}</p><p>Precio: {precio_recibido} USD</p>"

if __name__ == '__main__':
    app.run(debug=True)