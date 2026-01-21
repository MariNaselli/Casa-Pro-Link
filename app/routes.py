from flask import flash, render_template, request, redirect, url_for, session, current_app as app
from .models import Propiedad, Multimedia, db # <--- Agregamos Multimedia
import os
import uuid # Para generar nombres de archivos únicos
from werkzeug.utils import secure_filename

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
            Propiedad.activo == True, # <--- Agregamos esta condición
            (Propiedad.titulo.contains(query) 
             | Propiedad.calle.contains(query)
             | Propiedad.barrio.contains(query))
        ).all()
    else:
        # Si no hay búsqueda, traemos todas las que estén ACTIVA == True
        lista_propiedades = Propiedad.query.filter_by(activo=True).all()
        
    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar', methods=['GET', 'POST'])
def cargar():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 1. Creamos el objeto Propiedad
        nueva_propiedad = Propiedad(
            titulo=request.form.get('titulo'),
            precio=request.form.get('precio'),
            calle=request.form.get('calle'),
            altura=request.form.get('altura'),
            barrio=request.form.get('barrio'),
            moneda=request.form.get('moneda'), 
            operacion=request.form.get('operacion'),
            descripcion=request.form.get('descripcion'),
            m2_totales=request.form.get('m2_totales'),
            m2_cubiertos=request.form.get('m2_cubiertos'),
            dormitorios=request.form.get('dormitorios'),
            banios=request.form.get('banios'),
            propietario_nombre=request.form.get('propietario_nombre'),
            propietario_tel=request.form.get('propietario_tel'),
            activo=True 
        )
        
        db.session.add(nueva_propiedad)
        # IMPORTANTE: flush() genera el ID sin cerrar la sesión. 
        # Si hacés commit() acá, a veces se rompe la conexión para los archivos.
        db.session.flush() 

        # 2. PROCESAR IMÁGENES (Bucle for para que NO se pisen)
        imagenes = request.files.getlist('imagenes')
        for file in imagenes:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                # Nombre único con UUID para que no se pisen archivos iguales
                nombre_unico = f"{uuid.uuid4().hex}_{filename}"
                ruta = os.path.join(app.static_folder, 'uploads', nombre_unico)
                file.save(ruta)
                
                # Creamos una entrada en Multimedia por CADA imagen
                nuevo_m = Multimedia(
                    archivo_nombre=nombre_unico,
                    tipo='imagen',
                    propiedad_id=nueva_propiedad.id
                )
                db.session.add(nuevo_m)

        # 3. PROCESAR VIDEOS
        videos = request.files.getlist('videos')
        for video in videos:
            if video and video.filename != '':
                v_filename = secure_filename(video.filename)
                v_nombre_unico = f"{uuid.uuid4().hex}_{v_filename}"
                v_ruta = os.path.join(app.static_folder, 'uploads', v_nombre_unico)
                video.save(v_ruta)
                
                nuevo_v = Multimedia(
                    archivo_nombre=v_nombre_unico,
                    tipo='video',
                    propiedad_id=nueva_propiedad.id
                )
                db.session.add(nuevo_v)

        # 4. COMMIT FINAL (Guarda la casa y todos sus archivos juntos)
        db.session.commit()

        flash('Propiedad y archivos cargados con éxito', 'success')
        return redirect(url_for('home'))

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
    
    if request.method == 'POST':
        # Actualizar datos de texto (ya lo tenés)
        p.titulo = request.form.get('titulo')
        # ... todos los demás campos ...

        # Procesar NUEVAS imágenes (igual que en cargar)
        nuevas_fotos = request.files.getlist('imagenes')
        for file in nuevas_fotos:
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                nombre_unico = f"{uuid.uuid4().hex}_{filename}"
                file.save(os.path.join(app.static_folder, 'uploads', nombre_unico))
                
                nuevo_m = Multimedia(archivo_nombre=nombre_unico, tipo='imagen', propiedad_id=p.id)
                db.session.add(nuevo_m)

        db.session.commit()
        flash('Propiedad actualizada', 'success')
        return redirect(url_for('ficha', id=p.id))
        
    return render_template('editar.html', p=p)

@app.route('/borrar_archivo/<int:id>')
def borrar_archivo(id):
    archivo = Multimedia.query.get_or_404(id)
    propiedad_id = archivo.propiedad_id
    
    # Borrar archivo físico
    ruta = os.path.join(app.static_folder, 'uploads', archivo.archivo_nombre)
    if os.path.exists(ruta):
        os.remove(ruta)
    
    # Borrar de la base de datos
    db.session.delete(archivo)
    db.session.commit()
    
    flash('Archivo eliminado', 'info')
    return redirect(url_for('editar', id=propiedad_id))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    
    p = Propiedad.query.get_or_404(id)
    p.activo = False
    db.session.commit()
    flash('La propiedad ha sido eliminada correctamente.', 'warning')
    return redirect(url_for('home'))
