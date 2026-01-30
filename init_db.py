from app import create_app, db
from app.models import Usuario, TipoPropiedad, TipoOperacion, Barrio

app = create_app()

def seed():
    with app.app_context():
        # ESTA LÍNEA ES LA QUE FALTA: Crea las tablas si no existen
        db.create_all()
        # 1. Crear el Usuario Administrador
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(username='admin')
            admin.set_password('1234')
            db.session.add(admin)

        # 2. Poblar Tipos de Propiedad (Si no existen)
        tipos = ["Casa", "Departamento", "Duplex", "Terreno", "Local", "Oficina"]
        for t in tipos:
            if not TipoPropiedad.query.filter_by(nombre=t).first():
                db.session.add(TipoPropiedad(nombre=t))

        # 3. Poblar Operaciones
        ops = ["Venta", "Alquiler", "Alquiler Temporal"]
        for o in ops:
            if not TipoOperacion.query.filter_by(nombre=o).first():
                db.session.add(TipoOperacion(nombre=o))

        # 4. Poblar Barrios Iniciales
        barrios = ["Nueva Córdoba", "General Paz", "Centro", "Cerro de las Rosas", "Alberdi"]
        for b in barrios:
            if not Barrio.query.filter_by(nombre=b).first():
                db.session.add(Barrio(nombre=b))

        db.session.commit()
        print("¡Base de datos poblada con éxito!")

if __name__ == '__main__':
    seed()