from datetime import datetime
from energia_app.models.user import db
from sqlalchemy import Index

class SupportTicket(db.Model):
    """Modelo para tickets de soporte técnico"""
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # bug, feature, support, other
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed, resolved
    priority = db.Column(db.String(10), default='medium')  # low, medium, high, urgent
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    user = db.relationship('User', foreign_keys=[user_id], backref='created_tickets')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tickets')
    messages = db.relationship('TicketMessage', backref='ticket', lazy=True, 
                              cascade='all, delete-orphan', order_by='TicketMessage.created_at')
    attachments = db.relationship('TicketAttachment', backref='ticket', lazy=True,
                                cascade='all, delete-orphan')
    
    # Índices para mejorar rendimiento
    __table_args__ = (
        Index('idx_ticket_status_priority', 'status', 'priority'),
        Index('idx_ticket_user_created', 'user_id', 'created_at'),
        Index('idx_ticket_assigned', 'assigned_to', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
    
    def generate_ticket_number(self):
        """Genera un número único de ticket"""
        import random
        import string
        
        # Formato: UDEC-YYYY-XXXXXX
        year = datetime.now().year
        random_part = ''.join(random.choices(string.digits, k=6))
        return f"UDEC-{year}-{random_part}"
    
    def get_status_color(self):
        """Retorna el color Bootstrap para el estado"""
        colors = {
            'open': 'primary',
            'in_progress': 'warning',
            'resolved': 'success',
            'closed': 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Retorna el color Bootstrap para la prioridad"""
        colors = {
            'low': 'success',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'info')
    
    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar el ticket"""
        return (user.id == self.user_id or 
                user.id == self.assigned_to or 
                user.role == 'admin')
    
    def mark_as_resolved(self, resolved_by_user_id):
        """Marca el ticket como resuelto"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Crear mensaje automático
        message = TicketMessage(
            ticket_id=self.id,
            user_id=resolved_by_user_id,
            message="Ticket marcado como resuelto.",
            is_internal=False,
            is_system_message=True
        )
        db.session.add(message)
    
    def to_dict(self):
        """Convierte el ticket a diccionario para API"""
        return {
            'id': self.id,
            'ticket_number': self.ticket_number,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email
            },
            'assignee': {
                'id': self.assignee.id,
                'username': self.assignee.username
            } if self.assignee else None,
            'messages_count': len(self.messages)
        }

class TicketMessage(db.Model):
    """Modelo para mensajes dentro de tickets"""
    __tablename__ = 'ticket_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    is_internal = db.Column(db.Boolean, default=False)  # Mensaje interno para admins
    is_system_message = db.Column(db.Boolean, default=False)  # Mensaje automático del sistema
    edited_at = db.Column(db.DateTime, nullable=True)
    
    # Relaciones
    user = db.relationship('User', backref='ticket_messages')
    
    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar el mensaje"""
        # Solo el autor puede editar dentro de 5 minutos
        if user.id != self.user_id:
            return False
        
        time_limit = datetime.utcnow() - self.created_at
        return time_limit.total_seconds() < 300  # 5 minutos
    
    def to_dict(self):
        """Convierte el mensaje a diccionario para API"""
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'is_internal': self.is_internal,
            'is_system_message': self.is_system_message,
            'user': {
                'id': self.user.id,
                'username': self.user.username
            },
            'edited_at': self.edited_at.isoformat() if self.edited_at else None
        }

class TicketAttachment(db.Model):
    """Modelo para archivos adjuntos en tickets"""
    __tablename__ = 'ticket_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = db.relationship('User', backref='ticket_attachments')

class ChatMessage(db.Model):
    """Modelo para chat interno entre usuarios"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    is_system_message = db.Column(db.Boolean, default=False)
    
    # Relaciones
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    
    # Índices
    __table_args__ = (
        Index('idx_chat_sender_receiver', 'sender_id', 'receiver_id', 'created_at'),
        Index('idx_chat_unread', 'receiver_id', 'read_at'),
    )
    
    def mark_as_read(self):
        """Marca el mensaje como leído"""
        if not self.read_at:
            self.read_at = datetime.utcnow()
    
    def to_dict(self):
        """Convierte el mensaje a diccionario para API"""
        return {
            'id': self.id,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'sender': {
                'id': self.sender.id,
                'username': self.sender.username
            },
            'receiver': {
                'id': self.receiver.id,
                'username': self.receiver.username
            }
        }