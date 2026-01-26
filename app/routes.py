from flask import flash, render_template, request, redirect, url_for, current_app as app
from .models import Propiedad, Multimedia, db, Usuario, Propietario
from sqlalchemy.orm import joinedload
from flask_login import login_user, logout_user, login_required, current_user 
from .utils import guardar_archivo_multimedia # <--- IMPORTANTE


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: # Si ya está logueado, lo mandamos al home
        return redirect(url_for('home'))

    if request.method == 'POST':
        nombre_usuario = request.form.get('usuario')
        clave = request.form.get('clave')
        
        # Buscamos al usuario en la base de datos
        user = Usuario.query.filter_by(username=nombre_usuario).first()

        # Verificamos si existe y si la clave (hasheada) coincide
        if user and user.check_password(clave):
            login_user(user) # <--- Aquí ocurre la magia de la sesión segura
            return redirect(url_for('home'))
        else:
            flash('Usuario o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required # Solo alguien logueado puede desloguearse
def logout():
    logout_user() # Borra la sesión de forma segura
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():

    query = request.args.get('q', '')

    if query.strip():
        lista_propiedades = Propiedad.query.options(joinedload(Propiedad.archivos)).filter(
            Propiedad.activo == True,
            (Propiedad.titulo.contains(query)
             | Propiedad.calle.contains(query)
             | Propiedad.barrio.contains(query))
        ).all()
    else:
        lista_propiedades = Propiedad.query.options(joinedload(Propiedad.archivos)).filter_by(activo=True).all()

    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar', methods=['GET', 'POST'])
@login_required
def cargar():
    if request.method == 'POST':
        # 1. Instancia de Propiedad
        nueva_propiedad = Propiedad(
            titulo=request.form.get('titulo'),
            precio=request.form.get('precio'),
            moneda=request.form.get('moneda'),
            operacion=request.form.get('operacion'),
            calle=request.form.get('calle'),
            altura=request.form.get('altura'),
            barrio=request.form.get('barrio'),
            descripcion=request.form.get('descripcion'), 
            m2_totales=request.form.get('m2_totales'),
            m2_cubiertos=request.form.get('m2_cubiertos'),
            dormitorios=request.form.get('dormitorios'),
            banios=request.form.get('banios'),
            mostrar_inmo=request.form.get('mostrar_inmo') == 'on',
            cochera=request.form.get('cochera') == 'on',
            pileta=request.form.get('pileta') == 'on',
            quincho=request.form.get('quincho') == 'on',
            patio=request.form.get('patio') == 'on',
            activo=True
        )
        db.session.add(nueva_propiedad)
        db.session.flush() 

        # 2. PROCESAR PROPIETARIOS
        data_propietarios = zip(
            request.form.getlist('propietario_nombre[]'),
            request.form.getlist('propietario_tel[]'),
            request.form.getlist('propietario_email[]'),
            request.form.getlist('propietario_dni[]'),
            request.form.getlist('notas_legajo[]')
        )
        for n, t, e, d, nt in data_propietarios:
            if n.strip(): 
                db.session.add(Propietario(
                    nombre=n, telefono=t, email=e, dni=d, 
                    notas_legajo=nt, propiedad_id=nueva_propiedad.id
                ))

        # 3. PROCESAR MULTIMEDIA (Dinamismo puro)
        mapeo = {'imagenes': 'imagen', 'videos': 'video', 'documentos': 'documento'}
        
        for input_name, tipo_db in mapeo.items():
            for f in request.files.getlist(input_name):
                # Llamamos a la utilidad. Ella decide si optimizar o no.
                nombre_final = guardar_archivo_multimedia(
                    f, 
                    tipo_folder=('documentos' if tipo_db == 'documento' else 'uploads'),
                    optimizar=(tipo_db != 'video')
                )
                if nombre_final:
                    db.session.add(Multimedia(
                        archivo_nombre=nombre_final, 
                        tipo=tipo_db, 
                        propiedad_id=nueva_propiedad.id
                    ))

        db.session.commit()
        flash('Propiedad y Legajo cargados con éxito', 'success')
        return redirect(url_for('home'))

    return render_template('cargar.html')

@app.route('/propiedad/<int:id>')
def ficha(id):
    # Buscamos la propiedad
    propiedad = Propiedad.query.get_or_404(id)
    
    # Si la propiedad no está activa Y el usuario no es admin...
    if not propiedad.activo and not current_user.is_authenticated:
        # Lo mandamos a una página de error o al home
        flash("Esta propiedad ya no está disponible.", "info")
        return redirect(url_for('home'))
        
    return render_template('ficha.html', p=propiedad)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    # Eliminamos el chequeo manual de session, @login_required se encarga
    p = Propiedad.query.get_or_404(id)

    if request.method == 'POST':
        p.titulo = request.form.get('titulo')
        p.operacion = request.form.get('operacion')
        p.precio = request.form.get('precio')
        p.moneda = request.form.get('moneda')
        p.calle = request.form.get('calle')
        p.altura = request.form.get('altura')
        p.barrio = request.form.get('barrio')
        p.dormitorios = request.form.get('dormitorios')
        p.banios = request.form.get('banios')
        p.m2_totales = request.form.get('m2_totales')
        p.m2_cubiertos = request.form.get('m2_cubiertos')
        p.descripcion = request.form.get('descripcion')
        p.propietario_nombre = request.form.get('propietario_nombre')
        p.propietario_tel = request.form.get('propietario_tel')
        p.mostrar_inmo = request.form.get('mostrar_inmo') == 'on'

        # 2. Procesar NUEVAS IMÁGENES
        nuevas_fotos = request.files.getlist('imagenes')
        for file in nuevas_fotos:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                nombre_unico = f"{uuid.uuid4().hex}_{filename}"
                ruta_final = os.path.join(app.static_folder, 'uploads', nombre_unico)
                
                # Guardamos la imagen
                file.save(ruta_final)
                
                # --- NUEVO: OPTIMIZACIÓN EN EDICIÓN ---
                optimizar_imagen(ruta_final)
                
                nuevo_m = Multimedia(
                    archivo_nombre=nombre_unico, 
                    tipo='imagen', 
                    propiedad_id=p.id
                )
                db.session.add(nuevo_m)

        # 3. Procesar NUEVOS VIDEOS (Sin optimización de Pillow)
        nuevos_videos = request.files.getlist('videos')
        for video in nuevos_videos:
            if video and video.filename != '':
                v_filename = secure_filename(video.filename)
                v_nombre_unico = f"{uuid.uuid4().hex}_{v_filename}"
                video.save(os.path.join(app.static_folder, 'uploads', v_nombre_unico))
                
                nuevo_v = Multimedia(
                    archivo_nombre=v_nombre_unico, 
                    tipo='video', 
                    propiedad_id=p.id
                )
                db.session.add(nuevo_v)

        db.session.commit()
        flash('¡Propiedad actualizada con éxito!', 'success')
        return redirect(url_for('ficha', id=p.id))

    return render_template('editar.html', p=p)

@app.route('/borrar_archivo/<int:id>')
@login_required # <--- Siempre protegé estas rutas
def borrar_archivo(id):
    archivo = Multimedia.query.get_or_404(id)
    
    # Construimos la ruta absoluta al archivo
    ruta = os.path.join(app.static_folder, 'uploads', archivo.archivo_nombre)
    
    # Intentamos borrar el archivo físico
    try:
        if os.path.exists(ruta):
            os.remove(ruta)
            print(f"Archivo eliminado: {ruta}")
    except Exception as e:
        print(f"Error al borrar archivo físico: {e}")
        # Aunque falle el borrado físico (ej: archivo no existe), 
        # seguimos adelante para limpiar la base de datos.

    db.session.delete(archivo)
    db.session.commit()

    return {"status": "success"}, 200

@app.route('/eliminar/<int:id>')
@login_required # Flask-Login ya protege esta ruta
def eliminar(id):
    # Buscamos la propiedad
    p = Propiedad.query.get_or_404(id)
    
    # En lugar de borrarla de la base de datos, la desactivamos
    p.activo = False 
    
    # Guardamos el cambio
    db.session.commit()
    
    flash('La propiedad ha sido quitada de la lista pública (archivada).', 'warning')
    return redirect(url_for('home'))

@app.route('/toggle_inmo/<int:id>', methods=['POST'])
@login_required
def toggle_inmo(id):
    p = Propiedad.query.get_or_404(id)
    p.mostrar_inmo = not p.mostrar_inmo
    db.session.commit()
    return {"status": "success", "nuevo_estado": p.mostrar_inmo}
     
        
@app.route('/propiedad/legajo/<int:id>')
@login_required
def ver_legajo(id):
    propiedad = Propiedad.query.get_or_404(id)
    # Filtramos solo los archivos que marcamos como 'documento'
    documentos = [m for m in propiedad.archivos if m.tipo == 'documento']
    return render_template('legajo.html', p=propiedad, documentos=documentos)