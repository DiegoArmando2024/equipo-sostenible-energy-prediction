from functools import wraps
from flask import request, jsonify, current_app
from flask_login import current_user
from energia_app.services.encryption_service import JWTService, SecurityAuditService
import logging

logger = logging.getLogger(__name__)

def require_api_key(f):
    """Decorador para requerir API key en endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key requerida'}), 401
        
        # Verificar API key (implementar lógica según necesidades)
        valid_keys = current_app.config.get('VALID_API_KEYS', [])
        if api_key not in valid_keys:
            return jsonify({'error': 'API key inválida'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_jwt_token(f):
    """Decorador para requerir token JWT válido"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autorización requerido'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = JWTService.decode_token(token)
            request.jwt_payload = payload
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def log_security_event(event_type):
    """Decorador para registrar eventos de seguridad"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            audit_service = SecurityAuditService()
            
            # Ejecutar función
            result = f(*args, **kwargs)
            
            # Registrar evento
            try:
                user_id = getattr(current_user, 'id', None) if current_user.is_authenticated else None
                
                audit_service.log_security_event(
                    user_id=user_id,
                    event_type=event_type,
                    details={
                        'endpoint': request.endpoint,
                        'method': request.method,
                        'args': str(args),
                        'status': 'success'
                    },
                    ip_address=request.remote_addr
                )
                
            except Exception as e:
                logger.error(f"Error registrando evento de seguridad: {str(e)}")
            
            return result
        
        return decorated_function
    return decorator

def rate_limit(max_requests=100, window=3600):
    """Decorador para limitar número de requests"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementar lógica de rate limiting
            # (usando Redis o memoria en caché)
            
            # Por simplicidad, se omite la implementación completa
            # En producción, usar librerías como Flask-Limiter
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator