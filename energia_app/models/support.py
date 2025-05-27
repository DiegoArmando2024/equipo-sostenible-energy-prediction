from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from energia_app.models.user import db
from datetime import datetime
import logging
import random

logger = logging.getLogger(__name__)

def _get_encryption_service():
    """Importación tardía para evitar importación circular"""
    try:
        from energia_app.services import get_service
        return get_service('encryption')
    except ImportError:
        logger.warning("No se pudo importar el servicio de encriptación")
        return None

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    
    # Campo encriptado para la descripción
    _encrypted_description = db.Column('description', db.Text, nullable=False)
    
    category = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(20), default='medium')
    status = db.Column(db.String(20), default='open')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref='support_tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to])
    messages = db.relationship('TicketMessage', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        # Generar número de ticket único
        if 'ticket_number' not in kwargs:
            kwargs['ticket_number'] = self.generate_ticket_number()
        super().__init__(**kwargs)
    
    @staticmethod
    def generate_ticket_number():
        """Genera un número único para el ticket"""
        year = datetime.now().year
        random_num = random.randint(100000, 999999)
        return f"UDEC-{year}-{random_num}"
    
    # Propiedades para encriptar/desencriptar automáticamente
    @property
    def description(self):
        """Desencripta la descripción al leerla"""
        if not self._encrypted_description:
            return ""
        
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                return encryption_service.decrypt_sensitive_data(self._encrypted_description)
            else:
                # Si no hay servicio de encriptación, devolver tal como está
                return self._encrypted_description
        except Exception as e:
            logger.error(f"Error desencriptando descripción del ticket {self.id}: {str(e)}")
            return "[Error: No se puede desencriptar]"
    
    @description.setter
    def description(self, value):
        """Encripta la descripción al guardarla"""
        if not value:
            self._encrypted_description = ""
            return
            
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                self._encrypted_description = encryption_service.encrypt_sensitive_data(value)
                logger.info(f"Descripción encriptada para ticket")
            else:
                # Si no hay servicio de encriptación, guardar tal como está
                self._encrypted_description = value
                logger.warning("Servicio de encriptación no disponible, guardando sin encriptar")
        except Exception as e:
            logger.error(f"Error encriptando descripción del ticket: {str(e)}")
            self._encrypted_description = value
    
    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar este ticket"""
        return (user.id == self.user_id or 
                user.role == 'admin' or 
                user.id == self.assigned_to)
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,  # Automáticamente desencriptado
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username
            } if self.user else None,
            'assignee': {
                'id': self.assignee.id,
                'username': self.assignee.username
            } if self.assignee else None,
            'messages_count': self.messages.count()
        }

class TicketMessage(db.Model):
    __tablename__ = 'ticket_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Campo encriptado para el mensaje
    _encrypted_message = db.Column('message', db.Text, nullable=False)
    
    is_internal = db.Column(db.Boolean, default=False)
    is_system_message = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref='ticket_messages')
    
    # Propiedades para encriptar/desencriptar automáticamente
    @property
    def message(self):
        """Desencripta el mensaje al leerlo"""
        if not self._encrypted_message:
            return ""
        
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                return encryption_service.decrypt_sensitive_data(self._encrypted_message)
            else:
                return self._encrypted_message
        except Exception as e:
            logger.error(f"Error desencriptando mensaje {self.id}: {str(e)}")
            return "[Error: No se puede desencriptar]"
    
    @message.setter
    def message(self, value):
        """Encripta el mensaje al guardarlo"""
        if not value:
            self._encrypted_message = ""
            return
            
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                self._encrypted_message = encryption_service.encrypt_sensitive_data(value)
                logger.info(f"Mensaje encriptado para ticket {self.ticket_id}")
            else:
                self._encrypted_message = value
                logger.warning("Servicio de encriptación no disponible, guardando sin encriptar")
        except Exception as e:
            logger.error(f"Error encriptando mensaje: {str(e)}")
            self._encrypted_message = value
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'message': self.message,  # Automáticamente desencriptado  
            'is_internal': self.is_internal,
            'is_system_message': self.is_system_message,
            'created_at': self.created_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username
            } if self.user else None
        }

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Campo encriptado para el mensaje de chat
    _encrypted_message = db.Column('message', db.Text, nullable=False)
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    # Propiedades para encriptar/desencriptar automáticamente
    @property
    def message(self):
        """Desencripta el mensaje al leerlo"""
        if not self._encrypted_message:
            return ""
        
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                return encryption_service.decrypt_sensitive_data(self._encrypted_message)
            else:
                return self._encrypted_message
        except Exception as e:
            logger.error(f"Error desencriptando mensaje de chat {self.id}: {str(e)}")
            return "[Error: No se puede desencriptar]"
    
    @message.setter
    def message(self, value):
        """Encripta el mensaje al guardarlo"""
        if not value:
            self._encrypted_message = ""
            return
            
        try:
            encryption_service = _get_encryption_service()
            if encryption_service:
                self._encrypted_message = encryption_service.encrypt_sensitive_data(value)
                logger.info(f"Mensaje de chat encriptado")
            else:
                self._encrypted_message = value
                logger.warning("Servicio de encriptación no disponible para chat")
        except Exception as e:
            logger.error(f"Error encriptando mensaje de chat: {str(e)}")
            self._encrypted_message = value
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'message': self.message,  # Automáticamente desencriptado
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'sender': {
                'id': self.sender.id,
                'username': self.sender.username
            } if self.sender else None,
            'receiver': {
                'id': self.receiver.id,
                'username': self.receiver.username
            } if self.receiver else None
        }
        
class TicketAttachment(db.Model):
    __tablename__ = 'ticket_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    filesize = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ticket = db.relationship('SupportTicket', backref='attachments')