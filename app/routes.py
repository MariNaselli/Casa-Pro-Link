from flask import flash, render_template, request, redirect, url_for, session, current_app as app
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
        # Filtramos: que esté ACTIVA Y que coincida con la búsqueda
        lista_propiedades = Propiedad.query.filter(
            Propiedad.activo == True, # <--- Agregamos esta condición
            (Propiedad.titulo.contains(query) | Propiedad.ubicacion.contains(query))
        ).all()
    else:
        # Si no hay búsqueda, traemos todas las que estén ACTIVA == True
        lista_propiedades = Propiedad.query.filter_by(activo=True).all()
        
    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar')
@app.route('/cargar', methods=['GET', 'POST'])
def cargar():
    # 1. Seguridad: Solo si está logueado
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 2. Capturamos todos los datos (asegúrate que los 'name' coincidan con el HTML)
        nueva_propiedad = Propiedad(
            titulo=request.form.get('titulo'),
            precio=request.form.get('precio'),
            moneda=request.form.get('moneda'), 
            operacion=request.form.get('operacion'),
            ubicacion=request.form.get('ubicacion'),
            descripcion=request.form.get('descripcion'),
            m2_totales=request.form.get('m2_totales'),
            dormitorios=request.form.get('dormitorios'),
            banios=request.form.get('banios'),
            propietario_nombre=request.form.get('propietario_nombre'),
            propietario_tel=request.form.get('propietario_tel'),
            activo=True  # Para que aparezca en el home
        )

        # 3. Guardamos en la base de datos
        db.session.add(nueva_propiedad)
        db.session.commit()

        # 4. Avisamos y redirigimos al Home (ya no a una pantalla blanca)
        flash('¡Propiedad creada con éxito!', 'success')
        return redirect(url_for('home'))

    # Si es GET, simplemente mostramos el formulario
    return render_template('cargar.html')
@app.route('/propiedad/<int:id>')
def ficha(id):
    propiedad = Propiedad.query.get_or_404(id)
    return render_template('ficha.html', p=propiedad)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    p = Propiedad.query.get_or_404(id)
    origen = request.args.get('next', 'home')
    
    if request.method == 'POST':
        # 1. CAPTURAR los datos del formulario (Asegurate de que estos nombres coincidan con el 'name' de tus inputs en el HTML)
        p.titulo = request.form.get('titulo')
        p.ubicacion = request.form.get('ubicacion')
        p.precio = request.form.get('precio')
        p.moneda=request.form.get('moneda'), 
        p.operacion=request.form.get('operacion'),
        p.m2_totales = request.form.get('m2_totales')
        p.dormitorios = request.form.get('dormitorios')
        p.banios = request.form.get('banios')
        p.descripcion = request.form.get('descripcion')
        p.propietario_nombre = request.form.get('propietario_nombre')
        p.propietario_tel = request.form.get('propietario_tel')

        # 2. GUARDAR los cambios en la base de datos
        db.session.commit()
        
        # 3. AVISAR al usuario
        flash('¡Propiedad actualizada con éxito!', 'success')
        
        # 4. REDIRIGIR según el origen
        if origen == 'ficha':
            return redirect(url_for('ficha', id=p.id))
        return redirect(url_for('home'))
        
    return render_template('editar.html', p=p, origen=origen)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    p = Propiedad.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    flash('La propiedad ha sido eliminada correctamente.', 'warning')
    return redirect(url_for('home'))
