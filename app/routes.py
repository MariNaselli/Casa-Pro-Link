from flask import render_template, request, redirect, url_for, session, current_app as app
from .models import Propiedad, db

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        clave = request.form.get('clave')
     #Acceso temporal
    
        if usuario == 'admin' and clave == '1234':
            session['admin_logged_in'] = True
            return redirect(url_for('home'))
        else:
            return "Error: Usuario o contraseña incorrectos"
    
    return render_template('login.html')    

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))


@app.route('/')
def home():
    
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    query = request.args.get('q', '') 
    
    if query.strip():
        lista_propiedades = Propiedad.query.filter(
            (Propiedad.titulo.contains(query)) | 
            (Propiedad.ubicacion.contains(query))
        ).all()
    else:
        lista_propiedades = Propiedad.query.all()
        
    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar')
def cargar():
    return render_template('cargar.html')

@app.route('/procesar', methods=['POST'])
def procesar():
    titulo_recibido = request.form.get('titulo')
    precio_recibido = request.form.get('precio')
    ubicacion_recibida = request.form.get('ubicacion')
    propietario_recibido = request.form.get('propietario')
    
    nueva_propiedad = Propiedad(
        titulo=titulo_recibido, 
        precio=precio_recibido,
        ubicacion=ubicacion_recibida,
        propietario_nombre=propietario_recibido
        )
    
    db.session.add(nueva_propiedad)
    db.session.commit()
    
    return f"<h1>¡Guardado!</h1><p>Propiedad: {titulo_recibido} en {ubicacion_recibida} cargada correctamente.</p><a href='/cargar'>Cargar otra</a>"

@app.route('/propiedad/<int:id>')
def ficha(id):
    propiedad = Propiedad.query.get_or_404(id)
    return render_template('ficha.html', p=propiedad)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    propiedad = Propiedad.query.get_or_404(id)
    
    if request.method == 'POST':
        propiedad.titulo = request.form.get('titulo')
        propiedad.precio = request.form.get('precio')
        propiedad.ubicacion = request.form.get('ubicacion')
        propiedad.operacion = request.form.get('operacion')
        propiedad.descripcion = request.form.get('descripcion')
        propiedad.m2_totales = request.form.get('m2_totales')
        propiedad.dormitorios = request.form.get('dormitorios')
        propiedad.banios = request.form.get('banios')
        
        propiedad.propietario_nombre = request.form.get('propietario_nombre')
        propiedad.propietario_tel = request.form.get('propietario_tel')
        
        db.session.commit() 
        return redirect(url_for('ficha', id=propiedad.id))
    
    return render_template('editar.html', p=propiedad)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    p = Propiedad.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for('home'))