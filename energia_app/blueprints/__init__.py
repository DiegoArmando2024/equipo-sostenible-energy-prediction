# energia_app/blueprints/__init__.py
from flask import Blueprint
from flask_login import login_required, current_user
from energia_app.services import get_service
import logging

logger = logging.getLogger(__name__)

def register_blueprints(app):
    """Registra todos los blueprints en la aplicación Flask"""
    
    # Importar blueprints aquí para evitar importaciones circulares
    from .auth import auth_bp
    from .buildings import buildings_bp
    from .predictions import predictions_bp
    from .data_management import data_bp
    from .dashboard import dashboard_bp
    from .admin import admin_bp
    from .support import support_bp

    # Registrar blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(buildings_bp)
    app.register_blueprint(predictions_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(support_bp)

    logger.info("Todos los blueprints registrados correctamente")

# Exportar los blueprints para acceso directo si es necesario
from .auth import auth_bp
from .buildings import buildings_bp
from .predictions import predictions_bp
from .data_management import data_bp
from .dashboard import dashboard_bp
from .admin import admin_bp
from .support import support_bp

__all__ = [
    'register_blueprints',
    'auth_bp',
    'buildings_bp',
    'predictions_bp',
    'data_bp',
    'dashboard_bp',
    'admin_bp',
    'support_bp'
]