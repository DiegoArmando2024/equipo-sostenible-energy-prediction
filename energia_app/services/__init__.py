# energia_app/services/__init__.py
from flask import current_app
import logging

logger = logging.getLogger(__name__)

# Diccionario global para almacenar servicios
_services = {}

def init_services(app):
    """Inicializa todos los servicios de la aplicación"""
    global _services
    
    try:
        # Importar servicios aquí para evitar importaciones circulares
        from .email_service import EmailService
        from .encryption_service import EncryptionService, JWTService, SecurityAuditService
        from .support_service import SupportService
        
        # Configurar servicios principales
        email_service = EmailService(app)
        encryption_service = EncryptionService(app)
        
        _services = {
            'email': email_service,
            'encryption': encryption_service,
            'jwt': JWTService(),
            'security_audit': SecurityAuditService(),
            'support': SupportService()
        }
        
        # Inicializar el servicio de email en el contexto de la aplicación
        with app.app_context():
            email_service.init_app(app)
            encryption_service.init_app(app)
            
            # Configurar tareas programadas de email si APScheduler está disponible
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from .email_service import setup_scheduled_emails
                setup_scheduled_emails(app)
                logger.info("Tareas programadas de email configuradas")
            except ImportError:
                logger.warning("APScheduler no instalado. Tareas programadas deshabilitadas")
        
        # Almacenar en la extensión de la app para acceso global
        app.extensions['services'] = _services
        logger.info("Todos los servicios inicializados correctamente")
        
        return _services
        
    except Exception as e:
        logger.error(f"Error inicializando servicios: {str(e)}")
        raise

def get_service(name):
    """Obtiene un servicio por nombre
    
    Args:
        name (str): Nombre del servicio ('email', 'encryption', 'jwt', etc.)
        
    Returns:
        object: Instancia del servicio solicitado o None si no existe
    """
    try:
        # Primero intentar obtener de las extensiones de la app
        if current_app and hasattr(current_app, 'extensions'):
            return current_app.extensions['services'].get(name)
    except RuntimeError:
        # Fuera de contexto de aplicación, usar diccionario global
        pass
    
    # Fallback al diccionario global
    return _services.get(name)

def register_services_blueprints(app):
    """Registra blueprints relacionados con servicios si es necesario"""
    from energia_app.api import support_routes  # Importación relativa
    
    # Registrar blueprints de servicios
    app.register_blueprint(support_routes.support_bp)
    logger.info("Blueprints de servicios registrados")

# Exportar clases principales para acceso directo
from .email_service import EmailService
from .encryption_service import EncryptionService, JWTService, SecurityAuditService
from .support_service import SupportService

__all__ = [
    'init_services',
    'get_service',
    'register_services_blueprints',
    'EmailService',
    'EncryptionService',
    'JWTService',
    'SecurityAuditService',
    'SupportService'
]