from flask import render_template, request, redirect, url_for, session, current_app as app
from .models import Propiedad, db

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

@app.route('/propiedad/<int:id>')
def ficha(id):
    # Buscamos la propiedad por su ID, si no existe tira error 404
    propiedad = Propiedad.query.get_or_404(id)
    # Renderizamos el HTML de la ficha pasando la propiedad como 'p'
    return render_template('ficha.html', p=propiedad)