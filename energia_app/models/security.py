from datetime import datetime
from energia_app.models.user import db
from sqlalchemy import Index
import json
import logging

logger = logging.getLogger(__name__)

class SecurityLog(db.Model):
    """Modelo para registro de eventos de seguridad"""
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)
    encrypted_details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    user_agent = db.Column(db.String(500), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    
    # Relación con usuario
    user = db.relationship('User', backref='security_logs')
    
    # Índices para mejorar rendimiento de consultas
    __table_args__ = (
        Index('idx_security_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_security_event_timestamp', 'event_type', 'timestamp'),
        Index('idx_security_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def get_decrypted_details(self):
        """Obtiene los detalles desencriptados del evento"""
        if not self.encrypted_details:
            return {}
        
        try:
            from energia_app.services.encryption_service import EncryptionService
            encryption_service = EncryptionService()
            
            decrypted = encryption_service.decrypt_sensitive_data(self.encrypted_details)
            return json.loads(decrypted)
            
        except Exception as e:
            logger.error(f"Error desencriptando detalles de seguridad: {str(e)}")
            return {'error': 'No se pueden desencriptar los detalles'}
    
    def to_dict(self):
        """Convierte el log a diccionario para API"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'ip_address': self.ip_address,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
            'user': {
                'id': self.user.id,
                'username': self.user.username
            } if self.user else None
        }

class EncryptedUserData(db.Model):
    """Modelo para datos de usuario encriptados"""
    __tablename__ = 'encrypted_user_data'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # personal_info, preferences, etc.
    encrypted_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con usuario
    user = db.relationship('User', backref='encrypted_data')
    
    def set_data(self, data):
        """Encripta y almacena datos"""
        from energia_app.services.encryption_service import EncryptionService
        encryption_service = EncryptionService()
        
        self.encrypted_data = encryption_service.encrypt_sensitive_data(
            json.dumps(data) if isinstance(data, dict) else str(data)
        )
        self.updated_at = datetime.utcnow()
    
    def get_data(self):
        """Obtiene los datos desencriptados"""
        try:
            from energia_app.services.encryption_service import EncryptionService
            encryption_service = EncryptionService()
            
            decrypted = encryption_service.decrypt_sensitive_data(self.encrypted_data)
            
            # Intentar parsear como JSON
            try:
                return json.loads(decrypted)
            except json.JSONDecodeError:
                return decrypted
                
        except Exception as e:
            logger.error(f"Error desencriptando datos de usuario: {str(e)}")
            return None