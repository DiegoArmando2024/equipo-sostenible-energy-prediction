from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import os
import json
import logging
from datetime import datetime, timedelta
import jwt
from flask import current_app
import hashlib
import secrets

logger = logging.getLogger(__name__)

class EncryptionService:
    """Servicio de encriptación para datos sensibles"""
    
    def __init__(self, app=None):
        self.cipher = None
        self.rsa_private_key = None
        self.rsa_public_key = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa el servicio de encriptación con la aplicación Flask"""
        # Configurar clave simétrica
        self._setup_symmetric_encryption(app)
        
        # Configurar claves asimétricas (RSA)
        self._setup_asymmetric_encryption(app)
        
        # Configurar JWT
        app.config.setdefault('JWT_SECRET_KEY', os.environ.get('JWT_SECRET_KEY', 
                                                              secrets.token_urlsafe(32)))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
    
    def _setup_symmetric_encryption(self, app):
        """Configura la encriptación simétrica"""
        try:
            # Obtener clave maestra desde variable de entorno
            master_key = os.environ.get('MASTER_ENCRYPTION_KEY')
            
            if not master_key:
                # Generar nueva clave si no existe
                master_key = Fernet.generate_key().decode()
                logger.warning(f"Nueva clave de encriptación generada. Guardar en variable de entorno: {master_key}")
            
            # Derivar clave usando PBKDF2
            password = master_key.encode()
            salt = app.config.get('ENCRYPTION_SALT', 'udec_energy_system_2025').encode()
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password))
            self.cipher = Fernet(key)
            
            logger.info("Encriptación simétrica configurada correctamente")
            
        except Exception as e:
            logger.error(f"Error configurando encriptación simétrica: {str(e)}")
            raise
    
    def _setup_asymmetric_encryption(self, app):
        """Configura la encriptación asimétrica RSA"""
        try:
            private_key_path = app.config.get('RSA_PRIVATE_KEY_PATH', 'keys/private_key.pem')
            public_key_path = app.config.get('RSA_PUBLIC_KEY_PATH', 'keys/public_key.pem')
            
            # Crear directorio de claves si no existe
            os.makedirs(os.path.dirname(private_key_path), exist_ok=True)
            
            if os.path.exists(private_key_path) and os.path.exists(public_key_path):
                # Cargar claves existentes
                with open(private_key_path, 'rb') as f:
                    self.rsa_private_key = serialization.load_pem_private_key(
                        f.read(), password=None
                    )
                
                with open(public_key_path, 'rb') as f:
                    self.rsa_public_key = serialization.load_pem_public_key(f.read())
                    
                logger.info("Claves RSA cargadas desde archivos")
            else:
                # Generar nuevas claves RSA
                self.rsa_private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048
                )
                self.rsa_public_key = self.rsa_private_key.public_key()
                
                # Guardar claves en archivos
                with open(private_key_path, 'wb') as f:
                    f.write(self.rsa_private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ))
                
                with open(public_key_path, 'wb') as f:
                    f.write(self.rsa_public_key.public_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PublicFormat.SubjectPublicKeyInfo
                    ))
                
                logger.info("Nuevas claves RSA generadas y guardadas")
                
        except Exception as e:
            logger.error(f"Error configurando encriptación asimétrica: {str(e)}")
            raise
    
    def encrypt_sensitive_data(self, data):
        """
        Encripta datos sensibles usando encriptación simétrica
        
        Args:
            data (str or bytes): Datos a encriptar
            
        Returns:
            str: Datos encriptados en base64
        """
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            encrypted_data = self.cipher.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encriptando datos: {str(e)}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data):
        """
        Desencripta datos sensibles
        
        Args:
            encrypted_data (str): Datos encriptados en base64
            
        Returns:
            str: Datos desencriptados
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error desencriptando datos: {str(e)}")
            raise
    
    def encrypt_with_rsa(self, data):
        """
        Encripta datos usando RSA (para datos pequeños)
        
        Args:
            data (str): Datos a encriptar
            
        Returns:
            str: Datos encriptados en base64
        """
        try:
            encrypted = self.rsa_public_key.encrypt(
                data.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encriptando con RSA: {str(e)}")
            raise
    
    def decrypt_with_rsa(self, encrypted_data):
        """
        Desencripta datos usando RSA
        
        Args:
            encrypted_data (str): Datos encriptados en base64
            
        Returns:
            str: Datos desencriptados
        """
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.rsa_private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error desencriptando con RSA: {str(e)}")
            raise
    
    def generate_secure_token(self, length=32):
        """
        Genera un token seguro aleatorio
        
        Args:
            length (int): Longitud del token
            
        Returns:
            str: Token seguro
        """
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password, salt=None):
        """
        Genera hash seguro de contraseña usando PBKDF2
        
        Args:
            password (str): Contraseña a hashear
            salt (bytes): Salt opcional
            
        Returns:
            tuple: (hash, salt) en formato base64
        """
        if salt is None:
            salt = os.urandom(32)
        
        # Usar PBKDF2 con 100,000 iteraciones
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt, 
                                      100000)
        
        return (base64.b64encode(pwdhash).decode('utf-8'),
                base64.b64encode(salt).decode('utf-8'))
    
    def verify_password(self, password, stored_hash, stored_salt):
        """
        Verifica una contraseña contra su hash
        
        Args:
            password (str): Contraseña a verificar
            stored_hash (str): Hash almacenado en base64
            stored_salt (str): Salt almacenado en base64
            
        Returns:
            bool: True si la contraseña es correcta
        """
        try:
            salt = base64.b64decode(stored_salt.encode('utf-8'))
            stored_hash_bytes = base64.b64decode(stored_hash.encode('utf-8'))
            
            pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                          password.encode('utf-8'), 
                                          salt, 
                                          100000)
            
            return pwdhash == stored_hash_bytes
            
        except Exception as e:
            logger.error(f"Error verificando contraseña: {str(e)}")
            return False

class JWTService:
    """Servicio para manejo de JSON Web Tokens"""
    
    @staticmethod
    def generate_access_token(user_id, user_role='user'):
        """
        Genera un token de acceso JWT
        
        Args:
            user_id (int): ID del usuario
            user_role (str): Rol del usuario
            
        Returns:
            str: Token JWT
        """
        try:
            payload = {
                'user_id': user_id,
                'role': user_role,
                'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
                'iat': datetime.utcnow(),
                'type': 'access'
            }
            
            return jwt.encode(
                payload, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
        except Exception as e:
            logger.error(f"Error generando token de acceso: {str(e)}")
            raise
    
    @staticmethod
    def generate_refresh_token(user_id):
        """
        Genera un token de actualización JWT
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            str: Token JWT de actualización
        """
        try:
            payload = {
                'user_id': user_id,
                'exp': datetime.utcnow() + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
                'iat': datetime.utcnow(),
                'type': 'refresh'
            }
            
            return jwt.encode(
                payload, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithm='HS256'
            )
            
        except Exception as e:
            logger.error(f"Error generando token de actualización: {str(e)}")
            raise
    
    @staticmethod
    def decode_token(token):
        """
        Decodifica y valida un token JWT
        
        Args:
            token (str): Token JWT
            
        Returns:
            dict: Payload del token
        """
        try:
            return jwt.decode(
                token, 
                current_app.config['JWT_SECRET_KEY'], 
                algorithms=['HS256']
            )
            
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValueError("Token inválido")
        except Exception as e:
            logger.error(f"Error decodificando token: {str(e)}")
            raise ValueError("Error procesando token")

class SecurityAuditService:
    """Servicio para auditoría de seguridad"""
    
    def __init__(self):
        self.encryption_service = EncryptionService()
    
    def log_security_event(self, user_id, event_type, details, ip_address=None):
        """
        Registra un evento de seguridad
        
        Args:
            user_id (int): ID del usuario
            event_type (str): Tipo de evento
            details (dict): Detalles del evento
            ip_address (str): Dirección IP
        """
        try:
            from energia_app.models.security import SecurityLog
            
            # Encriptar detalles sensibles
            encrypted_details = self.encryption_service.encrypt_sensitive_data(
                json.dumps(details)
            )
            
            log_entry = SecurityLog(
                user_id=user_id,
                event_type=event_type,
                encrypted_details=encrypted_details,
                ip_address=ip_address,
                timestamp=datetime.utcnow()
            )
            
            from energia_app.models.user import db
            db.session.add(log_entry)
            db.session.commit()
            
            logger.info(f"Evento de seguridad registrado: {event_type} para usuario {user_id}")
            
        except Exception as e:
            logger.error(f"Error registrando evento de seguridad: {str(e)}")
    
    def check_suspicious_activity(self, user_id, activity_type):
        """
        Verifica actividad sospechosa
        
        Args:
            user_id (int): ID del usuario
            activity_type (str): Tipo de actividad
            
        Returns:
            bool: True si hay actividad sospechosa
        """
        try:
            from energia_app.models.security import SecurityLog
            
            # Verificar intentos fallidos en las últimas 24 horas
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_failures = SecurityLog.query.filter(
                SecurityLog.user_id == user_id,
                SecurityLog.event_type == f'{activity_type}_failed',
                SecurityLog.timestamp >= yesterday
            ).count()
            
            # Umbral de actividad sospechosa
            suspicious_threshold = {
                'login': 5,
                'password_change': 3,
                'data_access': 10
            }
            
            threshold = suspicious_threshold.get(activity_type, 5)
            return recent_failures >= threshold
            
        except Exception as e:
            logger.error(f"Error verificando actividad sospechosa: {str(e)}")
            return False
    
    def generate_security_report(self, start_date, end_date):
        """
        Genera reporte de seguridad
        
        Args:
            start_date (datetime): Fecha de inicio
            end_date (datetime): Fecha de fin
            
        Returns:
            dict: Reporte de seguridad
        """
        try:
            from energia_app.models.security import SecurityLog
            
            # Obtener eventos de seguridad en el período
            events = SecurityLog.query.filter(
                SecurityLog.timestamp >= start_date,
                SecurityLog.timestamp <= end_date
            ).all()
            
            # Análisis de eventos
            event_summary = {}
            user_activity = {}
            ip_addresses = set()
            
            for event in events:
                # Contar tipos de eventos
                event_summary[event.event_type] = event_summary.get(event.event_type, 0) + 1
                
                # Actividad por usuario
                if event.user_id:
                    user_activity[event.user_id] = user_activity.get(event.user_id, 0) + 1
                
                # Direcciones IP únicas
                if event.ip_address:
                    ip_addresses.add(event.ip_address)
            
            # Top usuarios más activos
            top_users = sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'total_events': len(events),
                'event_summary': event_summary,
                'unique_ips': len(ip_addresses),
                'top_active_users': top_users,
                'security_alerts': self._identify_security_alerts(events)
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de seguridad: {str(e)}")
            return {'error': str(e)}
    
    def _identify_security_alerts(self, events):
        """Identifica alertas de seguridad en los eventos"""
        alerts = []
        
        try:
            # Agrupar por usuario y tipo de evento
            user_events = {}
            for event in events:
                if event.user_id not in user_events:
                    user_events[event.user_id] = {}
                
                event_type = event.event_type
                if event_type not in user_events[event.user_id]:
                    user_events[event.user_id][event_type] = []
                
                user_events[event.user_id][event_type].append(event)
            
            # Identificar patrones sospechosos
            for user_id, events_by_type in user_events.items():
                # Múltiples fallos de login
                if 'login_failed' in events_by_type and len(events_by_type['login_failed']) >= 5:
                    alerts.append({
                        'type': 'multiple_login_failures',
                        'user_id': user_id,
                        'count': len(events_by_type['login_failed']),
                        'severity': 'high'
                    })
                
                # Acceso desde múltiples IPs
                if 'login_success' in events_by_type:
                    unique_ips = set(event.ip_address for event in events_by_type['login_success'] 
                                   if event.ip_address)
                    if len(unique_ips) > 3:
                        alerts.append({
                            'type': 'multiple_ip_access',
                            'user_id': user_id,
                            'ip_count': len(unique_ips),
                            'severity': 'medium'
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error identificando alertas de seguridad: {str(e)}")
            return []