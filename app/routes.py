from flask import flash, render_template, request, redirect, url_for, current_app as app
from .models import Propiedad, Multimedia, db, Usuario, Propietario, Barrio, TipoPropiedad, TipoOperacion
from sqlalchemy.orm import joinedload
from flask_login import login_user, logout_user, login_required, current_user 
from .utils import guardar_archivo_multimedia, generar_slug
import os
from sqlalchemy import or_

# --- FUNCIÓN MOTOR PARA BARRIOS (BUSCA O CREA) ---
def _obtener_o_crear_barrio(nombre_barrio):
    if not nombre_barrio:
        return None
    nombre_limpio = nombre_barrio.strip().title()
    barrio = Barrio.query.filter_by(nombre=nombre_limpio).first()
    if not barrio:
        barrio = Barrio(nombre=nombre_limpio)
        db.session.add(barrio)
        db.session.commit()
    return barrio.id

# --- AUTENTICACIÓN ---

@app.route('/admin')
def admin():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
    return render_template('admin/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- RUTAS PÚBLICAS ---

@app.route('/')
def home():
    q_general = request.args.get('q', '').strip()
    operacion_id = request.args.get('operacion')
    tipo_id = request.args.get('tipo')
    
    query = Propiedad.query.options(joinedload(Propiedad.archivos), joinedload(Propiedad.barrio_rel)).filter_by(activo=True)

    hay_busqueda = any([q_general, operacion_id, tipo_id])

    if hay_busqueda:
        if q_general:
            query = query.join(Barrio, isouter=True).filter(
                or_(Propiedad.titulo.ilike(f'%{q_general}%'), Barrio.nombre.ilike(f'%{q_general}%'), Propiedad.localidad.ilike(f'%{q_general}%'))
            )
        if operacion_id:
            query = query.filter(Propiedad.operacion_id == operacion_id)
        if tipo_id:
            query = query.filter(Propiedad.tipo_id == tipo_id)
    else:
        if not current_user.is_authenticated:
            query = query.filter_by(destacada=True)

    propiedades = query.order_by(Propiedad.fecha_carga.desc()).all()
    
    # Datos para buscadores y filtros
    tipos = TipoPropiedad.query.all()
    operaciones = TipoOperacion.query.all()
    sugerencias_barrios = [b.nombre for b in Barrio.query.all()]
    
    # Extraemos localidades únicas para el buscador inteligente de la home también
    ciudades_db = db.session.query(Propiedad.localidad).distinct().all()
    sugerencias_ciudades = [c[0] for c in ciudades_db if c[0]]

    return render_template('public/index.html', 
                           propiedades=propiedades, 
                           tipos=tipos, 
                           operaciones=operaciones,
                           sugerencias=sugerencias_barrios,
                           sugerencias_ciudades=sugerencias_ciudades,
                           hay_busqueda=hay_busqueda)

@app.route('/propiedad/<slug>')
def ficha(slug):
    propiedad = Propiedad.query.filter_by(slug=slug).first_or_404()
    if not propiedad.activo and not current_user.is_authenticated:
        flash("Esta propiedad ya no está disponible.", "info")
        return redirect(url_for('home'))
    return render_template('public/ficha.html', p=propiedad)

# --- GESTIÓN DE PROPIEDADES (ADMIN) ---

@app.route('/cargar', methods=['GET', 'POST'])
@login_required
def cargar():
    if request.method == 'POST':
        txt_titulo = request.form.get('titulo')
        nuevo_slug = generar_slug(txt_titulo)
        
        existe = Propiedad.query.filter_by(slug=nuevo_slug).first()
        if existe:
            flash(f'El título "{txt_titulo}" ya está en uso. Por favor elegí otro.', 'danger')
            return render_template('admin/formulario.html', 
                                   p=request.form, 
                                   tipos=TipoPropiedad.query.all(), 
                                   operaciones=TipoOperacion.query.all(), 
                                   barrios=Barrio.query.order_by(Barrio.nombre).all(),
                                   sugerencias=[b.nombre for b in Barrio.query.all()])

        try:
            nueva_propiedad = Propiedad(
                titulo=txt_titulo,
                slug=nuevo_slug,
                descripcion=request.form.get('descripcion'),
                tipo_id=request.form.get('tipo_id'),           
                operacion_id=request.form.get('operacion_id'), 
                barrio_id=_obtener_o_crear_barrio(request.form.get('barrio_nombre')),
                localidad=request.form.get('localidad'),
                calle=request.form.get('calle'),
                altura=request.form.get('altura'),
                precio=int(request.form.get('precio') or 0),
                moneda=request.form.get('moneda'),
                m2_totales=int(request.form.get('m2_totales') or 0),
                m2_cubiertos=int(request.form.get('m2_cubiertos') or 0),
                dormitorios=int(request.form.get('dormitorios') or 0),
                banios=int(request.form.get('banios') or 0),
                mostrar_inmo=request.form.get('mostrar_inmo') == 'on',
                destacada=request.form.get('destacada') == 'on',
                cochera=request.form.get('cochera') == 'on',
                pileta=request.form.get('pileta') == 'on',
                quincho=request.form.get('quincho') == 'on',
                patio=request.form.get('patio') == 'on',
                activo=True,
                estado='Disponible'
            )
            
            db.session.add(nueva_propiedad)
            db.session.flush() 
            _procesar_datos_adicionales(request, nueva_propiedad.id)
            db.session.commit()
            
            flash('Propiedad cargada con éxito', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar: {str(e)}', 'danger')
            return redirect(url_for('cargar'))

    # GET: Enviamos sugerencias de barrios y ciudades
    ciudades_db = db.session.query(Propiedad.localidad).distinct().all()
    sugerencias_ciudades = [c[0] for c in ciudades_db if c[0]]

    return render_template('admin/formulario.html', 
                           tipos=TipoPropiedad.query.all(), 
                           operaciones=TipoOperacion.query.all(), 
                           barrios=Barrio.query.order_by(Barrio.nombre).all(),
                           sugerencias=[b.nombre for b in Barrio.query.all()],
                           sugerencias_ciudades=sugerencias_ciudades)

@app.route('/check-slug')
@login_required
def check_slug():
    titulo = request.args.get('titulo', '')
    slug = generar_slug(titulo)
    existe = Propiedad.query.filter_by(slug=slug).first()
    return {"exists": existe is not None}

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    p = Propiedad.query.get_or_404(id)
    if request.method == 'POST':
        p.titulo = request.form.get('titulo')
        p.descripcion = request.form.get('descripcion')
        p.tipo_id = request.form.get('tipo_id')           
        p.operacion_id = request.form.get('operacion_id') 
        p.barrio_id = _obtener_o_crear_barrio(request.form.get('barrio_nombre'))
        
        p.precio = int(request.form.get('precio') or 0)
        p.moneda = request.form.get('moneda')
        p.localidad = request.form.get('localidad')
        p.calle = request.form.get('calle')
        p.altura = request.form.get('altura')
        p.dormitorios = int(request.form.get('dormitorios') or 0)
        p.banios = int(request.form.get('banios') or 0)
        p.m2_totales = int(request.form.get('m2_totales') or 0)
        p.m2_cubiertos = int(request.form.get('m2_cubiertos') or 0)
        
        p.mostrar_inmo = request.form.get('mostrar_inmo') == 'on'
        p.destacada = request.form.get('destacada') == 'on'
        p.cochera = request.form.get('cochera') == 'on'
        p.pileta = request.form.get('pileta') == 'on'
        p.quincho = request.form.get('quincho') == 'on'
        p.patio = request.form.get('patio') == 'on'

        Propietario.query.filter_by(propiedad_id=p.id).delete()
        _procesar_datos_adicionales(request, p.id)
        
        db.session.commit()
        flash('¡Propiedad actualizada!', 'success')
        return redirect(url_for('ficha', slug=p.slug))

    # GET: Sugerencias para el buscador inteligente
    ciudades_db = db.session.query(Propiedad.localidad).distinct().all()
    sugerencias_ciudades = [c[0] for c in ciudades_db if c[0]]

    return render_template('admin/formulario.html', p=p, 
                           tipos=TipoPropiedad.query.all(), 
                           operaciones=TipoOperacion.query.all(), 
                           barrios=Barrio.query.order_by(Barrio.nombre).all(),
                           sugerencias=[b.nombre for b in Barrio.query.all()],
                           sugerencias_ciudades=sugerencias_ciudades)

# --- FUNCIONES AUXILIARES ---

def _procesar_datos_adicionales(request, propiedad_id):
    nombres = request.form.getlist('propietario_nombre[]')
    tels = request.form.getlist('propietario_tel[]')
    emails = request.form.getlist('propietario_email[]')
    dnis = request.form.getlist('propietario_dni[]')
    notas = request.form.getlist('notas_legajo[]')

    for n, t, e, d, nt in zip(nombres, tels, emails, dnis, notas):
        if n.strip():
            db.session.add(Propietario(nombre=n, telefono=t, email=e, dni=d, notas_legajo=nt, propiedad_id=propiedad_id))

    mapeo = [
        ('imagenes', 'imagen', True),
        ('videos', 'video', False),
        ('video', 'video', False),
        ('documentos', 'documento', False)
    ]

    for input_name, tipo_db, debe_optimizar in mapeo:
        archivos = request.files.getlist(input_name)
        for f in archivos:
            if f and f.filename != '':
                nombre_en_disco = guardar_archivo_multimedia(f, tipo_folder='uploads', optimizar=debe_optimizar)
                if nombre_en_disco:
                    nueva_media = Multimedia(archivo_nombre=nombre_en_disco, tipo=tipo_db, propiedad_id=propiedad_id)
                    db.session.add(nueva_media)

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
    flash('Propiedad eliminada del catálogo.', 'warning')
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
    return render_template('admin/legajo.html', p=propiedad, documentos=documentos)

