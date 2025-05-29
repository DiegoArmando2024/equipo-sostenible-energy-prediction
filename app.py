# app.py
import os
import logging
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from energia_app.models.user import db, User
from energia_app.utils.scheduler import setup_scheduled_tasks
from energia_app.errors.handlers import register_error_handlers
from energia_app.services import init_services, get_service
from energia_app.blueprints import register_blueprints
from energia_app.services import register_services_blueprints

# Cargar variables de entorno
load_dotenv()

def create_app():
    """Factory principal para crear la aplicación Flask"""
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Crear aplicación Flask
    app = Flask(__name__, 
                template_folder='energia_app/templates',
                static_folder='energia_app/static')

    # Configuración de la aplicación
    configure_app(app)
    
    # Inicializar extensiones
    initialize_extensions(app)
    
    with app.app_context():
            db.create_all()
            # Crear usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'adminpassword'))
                db.session.add(admin)
                db.session.commit()
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Configurar manejo de errores
    register_error_handlers(app)
    
    # Configurar tareas programadas
    setup_scheduled_tasks(app)
    
    # Comandos CLI (opcional)
    register_commands(app)
    
    # Registrar blueprints de servicios
    register_services_blueprints(app)
    
    return app

def configure_app(app):
    """Configuración de la aplicación"""
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///energia_app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['ALLOWED_EXTENSIONS'] = {'csv'}
    
    # Configuración de Email - MOVER AQUÍ
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Crear directorios necesarios
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
            db.create_all()
            # Crear usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'adminpassword'))
                db.session.add(admin)
                db.session.commit()    
    

def initialize_extensions(app):
    """Inicializar extensiones Flask"""
    db.init_app(app)
    
    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Inicializar servicios
    from energia_app.services import init_services
    init_services(app)

def register_blueprints(app):
    from energia_app.blueprints.auth import auth_bp
    from energia_app.blueprints.buildings import buildings_bp
    from energia_app.blueprints.predictions import predictions_bp
    from energia_app.blueprints.data_management import data_bp
    from energia_app.blueprints.dashboard import dashboard_bp
    from energia_app.blueprints.admin import admin_bp
    from energia_app.blueprints.support import support_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(buildings_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(support_bp)
    
    @app.route('/test-encryption')
    def test_encryption():
        try:
            from energia_app.services import get_service
            
            encryption_service = get_service('encryption')
            if not encryption_service:
                return "Servicio de encriptación no disponible"
            
            # Probar encriptación
            test_data = "Este es un mensaje confidencial de prueba 🔒"
            
            # Encriptar
            encrypted = encryption_service.encrypt_sensitive_data(test_data)
            
            # Desencriptar
            decrypted = encryption_service.decrypt_sensitive_data(encrypted)
            
            return f"""
            <h2>Prueba de Encriptación</h2>
            <p><strong>Datos originales:</strong> {test_data}</p>
            <p><strong>Datos encriptados:</strong> {encrypted[:50]}...</p>
            <p><strong>Datos desencriptados:</strong> {decrypted}</p>
            <p><strong>¿Funciona?</strong> {'✅ SÍ' if test_data == decrypted else '❌ NO'}</p>
            """
            
        except Exception as e:
            return f"Error: {str(e)}"

def register_commands(app):
    """Registrar comandos CLI"""
    @app.cli.command('init-db')
    def init_db():
        """Inicializar la base de datos"""
        with app.app_context():
            db.create_all()
            # Crear usuario admin si no existe
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='admin'
                )
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'adminpassword'))
                db.session.add(admin)
                db.session.commit()
                print("Usuario administrador creado con éxito.")

# ✅ LÍNEA CLAVE AGREGADA: Crear la instancia global de la aplicación
# Esta línea es FUNDAMENTAL para que wsgi.py pueda importar 'app'
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)