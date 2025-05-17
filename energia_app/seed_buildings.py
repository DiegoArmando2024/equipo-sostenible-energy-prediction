"""
Script para crear edificios iniciales de prueba.
Para usar, ejecutar dentro del contexto de la aplicación:

python -c "from energia_app.seed_buildings import create_sample_buildings; create_sample_buildings()"

O alternativamente, inclúyelo en tu aplicación principal para ejecutarlo una vez:

from energia_app.seed_buildings import create_sample_buildings
with app.app_context():
    create_sample_buildings()
"""

from energia_app.models.user import db, Building

def create_sample_buildings():
    """
    Crea edificios de muestra para probar la aplicación.
    Solo crea los edificios si no existen ya en la base de datos.
    """
    # Verificar si ya existen edificios
    existing_buildings = Building.query.count()
    if existing_buildings > 0:
        print(f"Ya existen {existing_buildings} edificios en la base de datos. No se crearán más.")
        return
    
    # Lista de edificios de muestra
    sample_buildings = [
        {
            'name': 'Edificio Administrativo',
            'area': 2500.0,
            'location': 'Campus Principal - Zona Norte',
            'description': 'Edificio principal de administración que alberga oficinas para personal administrativo, rectoría y vicerrectoría.',
            'active': True
        },
        {
            'name': 'Biblioteca Central',
            'area': 3200.0,
            'location': 'Campus Principal - Zona Central',
            'description': 'Biblioteca principal con salas de estudio, colecciones de libros y recursos digitales.',
            'active': True
        },
        {
            'name': 'Facultad de Ingeniería',
            'area': 4100.0,
            'location': 'Campus Principal - Zona Sur',
            'description': 'Edificio de la Facultad de Ingeniería con aulas, laboratorios y oficinas para profesores.',
            'active': True
        },
        {
            'name': 'Cafetería Central',
            'area': 950.0,
            'location': 'Campus Principal - Zona Central',
            'description': 'Edificio destinado a servicios de alimentación para estudiantes y personal.',
            'active': True
        },
        {
            'name': 'Auditorio Principal',
            'area': 1800.0,
            'location': 'Campus Principal - Zona Este',
            'description': 'Auditorio para eventos académicos, conferencias y actividades culturales.',
            'active': True
        },
        {
            'name': 'Centro Deportivo',
            'area': 5600.0,
            'location': 'Campus Principal - Zona Oeste',
            'description': 'Complejo deportivo con gimnasio, canchas múltiples y áreas de entrenamiento.',
            'active': True
        },
        {
            'name': 'Laboratorios de Ciencias',
            'area': 2800.0,
            'location': 'Campus Principal - Zona Sur',
            'description': 'Edificio con laboratorios especializados para física, química y biología.',
            'active': True
        }
    ]
    
    # Crear edificios en la base de datos
    for building_data in sample_buildings:
        building = Building(**building_data)
        db.session.add(building)
    
    # Guardar cambios
    db.session.commit()
    print(f"Se han creado {len(sample_buildings)} edificios de muestra en la base de datos.")