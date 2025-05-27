# energia_app/errors/handlers.py
from flask import Blueprint, render_template, request, jsonify

# Un blueprint opcional para manejar errores, si quieres usarlo
errors_bp = Blueprint('errors', __name__)

def register_error_handlers(app):
    """Registra manejadores de errores globales para la aplicación Flask."""

    @app.errorhandler(400)
    def bad_request_error(error):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            response = jsonify({'error': 'Bad Request', 'message': str(error)})
            response.status_code = 400
            return response
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            response = jsonify({'error': 'Unauthorized', 'message': str(error)})
            response.status_code = 401
            return response
        return render_template('errors/401.html'), 401 # O redirigir al login

    @app.errorhandler(403)
    def forbidden_error(error):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            response = jsonify({'error': 'Forbidden', 'message': str(error)})
            response.status_code = 403
            return response
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            response = jsonify({'error': 'Not Found', 'message': str(error)})
            response.status_code = 404
            return response
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        # db.session.rollback() # Si usas Flask-SQLAlchemy y quieres revertir la sesión en caso de error
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            response = jsonify({'error': 'Internal Server Error', 'message': str(error)})
            response.status_code = 500
            return response
        return render_template('errors/500.html'), 500

    # Opcional: Registrar el blueprint si lo defines
    # app.register_blueprint(errors_bp)
    print("Manejadores de errores registrados.") # Para depuración

# Si vas a usar un blueprint solo para errores, el código sería diferente.
# Pero para registrar error handlers directamente en la app, la función es suficiente.