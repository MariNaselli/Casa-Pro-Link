from flask import flash, render_template, request, redirect, url_for, current_app as app
from .models import Propiedad, Multimedia, db, Usuario, Propietario
from sqlalchemy.orm import joinedload
from flask_login import login_user, logout_user, login_required, current_user 
from .utils import guardar_archivo_multimedia
import os
import uuid
from werkzeug.utils import secure_filename

@app.route('/admin')
def admin():
    # Si ya inició sesión, lo mandamos al home (donde verá sus botones)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    # Si no está logueado, lo mandamos directo al login
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        user = Usuario.query.filter_by(username=request.form.get('usuario')).first()
        if user and user.check_password(request.form.get('clave')):
            login_user(user)
            return redirect(url_for('home'))
        flash('Usuario o contraseña incorrectos', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
def home():
    query = request.args.get('q', '')
    if query.strip():
        lista_propiedades = Propiedad.query.options(joinedload(Propiedad.archivos)).filter(
            Propiedad.activo == True,
            (Propiedad.titulo.contains(query) | Propiedad.calle.contains(query) | Propiedad.barrio.contains(query))
        ).all()
    else:
        lista_propiedades = Propiedad.query.options(joinedload(Propiedad.archivos)).filter_by(activo=True).all()
    return render_template('index.html', propiedades=lista_propiedades, busqueda=query)

@app.route('/cargar', methods=['GET', 'POST'])
@login_required
def cargar():
    if request.method == 'POST':
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

        _procesar_datos_adicionales(request, nueva_propiedad.id)

        db.session.commit()
        flash('Propiedad cargada con éxito', 'success')
        return redirect(url_for('home'))
    return render_template('cargar.html')

@app.route('/propiedad/<int:id>')
def ficha(id):
    propiedad = Propiedad.query.get_or_404(id)
    if not propiedad.activo and not current_user.is_authenticated:
        flash("Esta propiedad ya no está disponible.", "info")
        return redirect(url_for('home'))
    return render_template('ficha.html', p=propiedad)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
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
        p.mostrar_inmo = request.form.get('mostrar_inmo') == 'on'
        p.cochera = request.form.get('cochera') == 'on'
        p.pileta = request.form.get('pileta') == 'on'
        p.quincho = request.form.get('quincho') == 'on'
        p.patio = request.form.get('patio') == 'on'

        # Actualizar Propietarios (Borrar y recrear para evitar duplicados)
        Propietario.query.filter_by(propiedad_id=p.id).delete()
        _procesar_datos_adicionales(request, p.id)

        db.session.commit()
        flash('¡Propiedad actualizada con éxito!', 'success')
        return redirect(url_for('ficha', id=p.id))
    return render_template('editar.html', p=p)

# Función interna para no repetir código entre cargar y editar
def _procesar_datos_adicionales(request, propiedad_id):
    # 1. Propietarios
    data_propietarios = zip(
        request.form.getlist('propietario_nombre[]'),
        request.form.getlist('propietario_tel[]'),
        request.form.getlist('propietario_email[]'),
        request.form.getlist('propietario_dni[]'),
        request.form.getlist('notas_legajo[]')
    )
    for n, t, e, d, nt in data_propietarios:
        if n.strip():
            db.session.add(Propietario(nombre=n, telefono=t, email=e, dni=d, notas_legajo=nt, propiedad_id=propiedad_id))

    # 2. Multimedia
    mapeo = {'imagenes': 'imagen', 'videos': 'video', 'documentos': 'documento'}
    for input_name, tipo_db in mapeo.items():
        for f in request.files.getlist(input_name):
            nombre = guardar_archivo_multimedia(f, tipo_folder=('documentos' if tipo_db == 'documento' else 'uploads'), optimizar=(tipo_db != 'video'))
            if nombre:
                db.session.add(Multimedia(archivo_nombre=nombre, tipo=tipo_db, propiedad_id=propiedad_id))

@app.route('/borrar_archivo/<int:id>', methods=['POST'])
@login_required
def borrar_archivo(id):
    archivo = Multimedia.query.get_or_404(id)
    ruta = os.path.join(app.static_folder, 'uploads', archivo.archivo_nombre)
    try:
        if os.path.exists(ruta): os.remove(ruta)
    except Exception as e: print(f"Error borrar físico: {e}")
    db.session.delete(archivo)
    db.session.commit()
    return {"status": "success"}, 200

@app.route('/eliminar/<int:id>')
@login_required
def eliminar(id):
    p = Propiedad.query.get_or_404(id)
    p.activo = False 
    db.session.commit()
    flash('Propiedad eliminada.', 'warning')
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
    documentos = [m for m in propiedad.archivos if m.tipo == 'documento']
    return render_template('legajo.html', p=propiedad, documentos=documentos)