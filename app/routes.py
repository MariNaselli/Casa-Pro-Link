from flask import flash, render_template, request, redirect, url_for, current_app as app
from .models import Propiedad, Multimedia, db, Usuario, Propietario, Barrio, TipoPropiedad, TipoOperacion
from sqlalchemy.orm import joinedload
from flask_login import login_user, logout_user, login_required, current_user 
from .utils import guardar_archivo_multimedia, generar_slug
import os
from sqlalchemy import or_

# --- FUNCIÓN AUXILIAR PARA BARRIOS ---
def _obtener_o_crear_barrio(nombre_barrio):
    if not nombre_barrio: return None
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
    if current_user.is_authenticated: return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('home'))
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
        if operacion_id: query = query.filter(Propiedad.operacion_id == operacion_id)
        if tipo_id: query = query.filter(Propiedad.tipo_id == tipo_id)
    else:
        if not current_user.is_authenticated:
            query = query.filter_by(destacada=True)

    propiedades = query.order_by(Propiedad.fecha_carga.desc()).all()
    return render_template('public/index.html', propiedades=propiedades, tipos=TipoPropiedad.query.all(), operaciones=TipoOperacion.query.all(), hay_busqueda=hay_busqueda)

@app.route('/propiedad/<slug>')
def ficha(slug):
    propiedad = Propiedad.query.filter_by(slug=slug).first_or_404()
    if not propiedad.activo and not current_user.is_authenticated:
        flash("Esta propiedad ya no está disponible.", "info")
        return redirect(url_for('home'))
    return render_template('public/ficha.html', p=propiedad)

# --- GESTIÓN DE PROPIEDADES ---
@app.route('/cargar', methods=['GET', 'POST'])
@login_required
def cargar():
    if request.method == 'POST':
        txt_titulo = request.form.get('titulo')
        nuevo_slug = generar_slug(txt_titulo)
        if Propiedad.query.filter_by(slug=nuevo_slug).first():
            flash('El título ya existe, elegí otro.', 'danger')
            return redirect(url_for('cargar'))

        try:
            nueva_p = Propiedad(
                titulo=txt_titulo, slug=nuevo_slug, descripcion=request.form.get('descripcion'),
                tipo_id=request.form.get('tipo_id'), operacion_id=request.form.get('operacion_id'),
                barrio_id=_obtener_o_crear_barrio(request.form.get('barrio_nombre')),
                localidad=request.form.get('localidad'), calle=request.form.get('calle'), altura=request.form.get('altura'),
                codigo_postal=request.form.get('codigo_postal'),
                latitud=float(request.form.get('latitud')) if request.form.get('latitud') else None,
                longitud=float(request.form.get('longitud')) if request.form.get('longitud') else None,
                precio=int(request.form.get('precio') or 0), moneda=request.form.get('moneda'),
                m2_totales=int(request.form.get('m2_totales') or 0), m2_cubiertos=int(request.form.get('m2_cubiertos') or 0),
                dormitorios=int(request.form.get('dormitorios') or 0), banios=int(request.form.get('banios') or 0),
                destacada=request.form.get('destacada') == 'on', cochera=request.form.get('cochera') == 'on',
                quincho=request.form.get('quincho') == 'on',
                patio=request.form.get('patio') == 'on', terraza=request.form.get('terraza') == 'on', balcon=request.form.get('balcon') == 'on',
                sum=request.form.get('sum') == 'on', gimnasio=request.form.get('gimnasio') == 'on', piscina=request.form.get('piscina') == 'on',
                
                activo=True, estado='Disponible'
            )
            db.session.add(nueva_p)
            db.session.flush() 
            _procesar_datos_adicionales(request, nueva_p.id)
            db.session.commit()
            flash('Propiedad cargada!', 'success')
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('cargar'))
    return render_template('admin/formulario.html', tipos=TipoPropiedad.query.all(), operaciones=TipoOperacion.query.all())

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    p = Propiedad.query.get_or_404(id)
    if request.method == 'POST':
        p.titulo, p.descripcion = request.form.get('titulo'), request.form.get('descripcion')
        p.tipo_id, p.operacion_id = request.form.get('tipo_id'), request.form.get('operacion_id')
        p.barrio_id = _obtener_o_crear_barrio(request.form.get('barrio_nombre'))
        p.codigo_postal = request.form.get('codigo_postal')
        p.localidad, p.calle, p.altura = request.form.get('localidad'), request.form.get('calle'), request.form.get('altura')
        p.latitud = float(request.form.get('latitud')) if request.form.get('latitud') else None
        p.longitud = float(request.form.get('longitud')) if request.form.get('longitud') else None
        p.precio, p.moneda = int(request.form.get('precio') or 0), request.form.get('moneda')
        p.dormitorios, p.banios = int(request.form.get('dormitorios') or 0), int(request.form.get('banios') or 0)
        p.m2_totales, p.m2_cubiertos = int(request.form.get('m2_totales') or 0), int(request.form.get('m2_cubiertos') or 0)
        p.destacada, p.cochera, = request.form.get('destacada')=='on', request.form.get('cochera')=='on', request.form.get('pileta')=='on'
        p.quincho, p.patio, p.terraza, p.balcon, p.sum, p.gimnasio, p.piscina= request.form.get('quincho')=='on', request.form.get('patio')=='on', request.form.get('terraza')=='on', request.form.get('balcon')=='on'
        
        Propietario.query.filter_by(propiedad_id=p.id).delete()
        _procesar_datos_adicionales(request, p.id)
        db.session.commit()
        flash('Actualizada!', 'success')
        return redirect(url_for('ficha', slug=p.slug))
    return render_template('admin/formulario.html', p=p, tipos=TipoPropiedad.query.all(), operaciones=TipoOperacion.query.all())

@app.route('/propiedad/legajo/<int:id>')
@login_required
def ver_legajo(id):
    propiedad = Propiedad.query.get_or_404(id)
    documentos = [m for m in propiedad.archivos if m.tipo == 'documento']
    return render_template('admin/legajo.html', p=propiedad, documentos=documentos)

@app.route('/check-slug')
@login_required
def check_slug():
    titulo = request.args.get('titulo', '')
    slug = generar_slug(titulo)
    existe = Propiedad.query.filter_by(slug=slug).first()
    return {"exists": existe is not None}

def _procesar_datos_adicionales(request, propiedad_id):
    # Propietarios con EMAIL corregido
    nombres = request.form.getlist('propietario_nombre[]')
    tels = request.form.getlist('propietario_tel[]')
    emails = request.form.getlist('propietario_email[]')
    notas = request.form.getlist('notas_legajo[]')
    for n, t, e, nt in zip(nombres, tels, emails, notas):
        if n.strip():
            db.session.add(Propietario(nombre=n, telefono=t, email=e, notas_legajo=nt, propiedad_id=propiedad_id))

    mapeo = [('imagenes', 'imagen', True), ('videos', 'video', False), ('documentos', 'documento', False)]
    for input_name, tipo_db, debe_optimizar in mapeo:
        for f in request.files.getlist(input_name):
            if f and f.filename != '':
                nombre = guardar_archivo_multimedia(f, tipo_folder='uploads', optimizar=debe_optimizar)
                if nombre: db.session.add(Multimedia(archivo_nombre=nombre, tipo=tipo_db, propiedad_id=propiedad_id))

@app.route('/borrar_archivo/<int:id>', methods=['POST'])
@login_required
def borrar_archivo(id):
    archivo = Multimedia.query.get_or_404(id)
    ruta = os.path.join(app.static_folder, 'uploads', archivo.archivo_nombre)
    try:
        if os.path.exists(ruta): os.remove(ruta)
    except: pass
    db.session.delete(archivo)
    db.session.commit()
    return {"status": "success"}, 200

@app.route('/eliminar/<int:id>')
@login_required
def eliminar(id):
    p = Propiedad.query.get_or_404(id)
    p.activo = False 
    db.session.commit()
    flash('Eliminada.', 'warning')
    return redirect(url_for('home'))
