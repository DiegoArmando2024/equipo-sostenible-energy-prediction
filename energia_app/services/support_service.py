from flask import current_app, request
from energia_app.models.support import SupportTicket, TicketMessage, ChatMessage
from energia_app.models.user import User, db
from energia_app.services.email_service import EmailService
import logging
import os
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SupportService:
    """Servicio para gestión de tickets de soporte y mensajería"""
    
    def __init__(self):
        self.email_service = EmailService()
        self.allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def create_ticket(self, user_id, title, description, category, priority='medium'):
        """
        Crea un nuevo ticket de soporte
        
        Args:
            user_id (int): ID del usuario que crea el ticket
            title (str): Título del ticket
            description (str): Descripción del problema
            category (str): Categoría del ticket
            priority (str): Prioridad del ticket
            
        Returns:
            SupportTicket: Ticket creado
        """
        try:
            ticket = SupportTicket(
                user_id=user_id,
                title=title,
                description=description,
                category=category,
                priority=priority
            )
            
            db.session.add(ticket)
            db.session.commit()
            
            # Crear mensaje inicial automático
            initial_message = TicketMessage(
                ticket_id=ticket.id,
                user_id=user_id,
                message=description,
                is_system_message=True
            )
            db.session.add(initial_message)
            db.session.commit()
            
            # Notificar a administradores
            self._notify_admins_new_ticket(ticket)
            
            logger.info(f"Ticket creado: {ticket.ticket_number} por usuario {user_id}")
            return ticket
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear ticket: {str(e)}")
            raise
    
    def add_message_to_ticket(self, ticket_id, user_id, message, is_internal=False):
        """
        Añade un mensaje a un ticket existente
        
        Args:
            ticket_id (int): ID del ticket
            user_id (int): ID del usuario que envía el mensaje
            message (str): Contenido del mensaje
            is_internal (bool): Si es un mensaje interno para admins
            
        Returns:
            TicketMessage: Mensaje creado
        """
        try:
            ticket = SupportTicket.query.get_or_404(ticket_id)
            
            # Verificar permisos
            user = User.query.get(user_id)
            if not ticket.can_be_edited_by(user):
                raise PermissionError("No tiene permisos para agregar mensajes a este ticket")
            
            ticket_message = TicketMessage(
                ticket_id=ticket_id,
                user_id=user_id,
                message=message,
                is_internal=is_internal
            )
            
            # Actualizar timestamp del ticket
            ticket.updated_at = datetime.utcnow()
            
            # Si el ticket estaba cerrado, reabrirlo
            if ticket.status == 'closed':
                ticket.status = 'open'
            
            db.session.add(ticket_message)
            db.session.commit()
            
            # Notificar a los involucrados
            self._notify_ticket_update(ticket, ticket_message)
            
            logger.info(f"Mensaje añadido al ticket {ticket.ticket_number}")
            return ticket_message
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al añadir mensaje al ticket: {str(e)}")
            raise
    
    def assign_ticket(self, ticket_id, assigned_to_user_id, assigned_by_user_id):
        """
        Asigna un ticket a un usuario
        
        Args:
            ticket_id (int): ID del ticket
            assigned_to_user_id (int): ID del usuario asignado
            assigned_by_user_id (int): ID del usuario que asigna
        """
        try:
            ticket = SupportTicket.query.get_or_404(ticket_id)
            assignee = User.query.get_or_404(assigned_to_user_id)
            
            # Verificar permisos (solo admins pueden asignar)
            assigner = User.query.get(assigned_by_user_id)
            if assigner.role != 'admin':
                raise PermissionError("Solo los administradores pueden asignar tickets")
            
            old_assignee_id = ticket.assigned_to
            ticket.assigned_to = assigned_to_user_id
            ticket.status = 'in_progress'
            ticket.updated_at = datetime.utcnow()
            
            # Crear mensaje automático
            message = TicketMessage(
                ticket_id=ticket_id,
                user_id=assigned_by_user_id,
                message=f"Ticket asignado a {assignee.username}",
                is_system_message=True
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Notificar al nuevo asignado
            self._notify_ticket_assignment(ticket, assignee)
            
            logger.info(f"Ticket {ticket.ticket_number} asignado a {assignee.username}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al asignar ticket: {str(e)}")
            raise
    
    def update_ticket_status(self, ticket_id, new_status, user_id):
        """
        Actualiza el estado de un ticket
        
        Args:
            ticket_id (int): ID del ticket
            new_status (str): Nuevo estado
            user_id (int): ID del usuario que actualiza
        """
        try:
            ticket = SupportTicket.query.get_or_404(ticket_id)
            user = User.query.get(user_id)
            
            if not ticket.can_be_edited_by(user):
                raise PermissionError("No tiene permisos para actualizar este ticket")
            
            old_status = ticket.status
            ticket.status = new_status
            ticket.updated_at = datetime.utcnow()
            
            if new_status == 'resolved':
                ticket.resolved_at = datetime.utcnow()
            
            # Crear mensaje automático
            message = TicketMessage(
                ticket_id=ticket_id,
                user_id=user_id,
                message=f"Estado cambiado de '{old_status}' a '{new_status}'",
                is_system_message=True
            )
            
            db.session.add(message)
            db.session.commit()
            
            # Notificar cambio de estado
            self._notify_status_change(ticket, old_status, new_status)
            
            logger.info(f"Estado del ticket {ticket.ticket_number} cambiado a {new_status}")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al actualizar estado del ticket: {str(e)}")
            raise
    
    def get_tickets_for_user(self, user_id, status_filter=None, page=1, per_page=20):
        """
        Obtiene tickets para un usuario específico
        
        Args:
            user_id (int): ID del usuario
            status_filter (str): Filtro de estado (opcional)
            page (int): Página para paginación
            per_page (int): Elementos por página
            
        Returns:
            Pagination: Objeto de paginación con tickets
        """
        user = User.query.get(user_id)
        query = SupportTicket.query
        
        if user.role == 'admin':
            # Admins ven todos los tickets
            pass
        else:
            # Usuarios normales solo ven sus tickets
            query = query.filter_by(user_id=user_id)
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        return query.order_by(SupportTicket.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    def send_chat_message(self, sender_id, receiver_id, message):
        """
        Envía un mensaje de chat entre usuarios
        
        Args:
            sender_id (int): ID del remitente
            receiver_id (int): ID del destinatario
            message (str): Contenido del mensaje
            
        Returns:
            ChatMessage: Mensaje creado
        """
        try:
            chat_message = ChatMessage(
                sender_id=sender_id,
                receiver_id=receiver_id,
                message=message
            )
            
            db.session.add(chat_message)
            db.session.commit()
            
            logger.info(f"Mensaje de chat enviado de {sender_id} a {receiver_id}")
            return chat_message
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al enviar mensaje de chat: {str(e)}")
            raise
    
    def get_chat_messages(self, user1_id, user2_id, page=1, per_page=50):
        """
        Obtiene mensajes de chat entre dos usuarios
        
        Args:
            user1_id (int): ID del primer usuario
            user2_id (int): ID del segundo usuario
            page (int): Página para paginación
            per_page (int): Mensajes por página
            
        Returns:
            list: Lista de mensajes ordenados por fecha
        """
        messages = ChatMessage.query.filter(
            ((ChatMessage.sender_id == user1_id) & (ChatMessage.receiver_id == user2_id)) |
            ((ChatMessage.sender_id == user2_id) & (ChatMessage.receiver_id == user1_id))
        ).order_by(ChatMessage.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Marcar mensajes como leídos
        unread_messages = ChatMessage.query.filter(
            ChatMessage.sender_id == user2_id,
            ChatMessage.receiver_id == user1_id,
            ChatMessage.read_at.is_(None)
        ).all()
        
        for msg in unread_messages:
            msg.mark_as_read()
        
        if unread_messages:
            db.session.commit()
        
        return messages
    
    def get_unread_messages_count(self, user_id):
        """
        Obtiene el número de mensajes no leídos para un usuario
        
        Args:
            user_id (int): ID del usuario
            
        Returns:
            int: Número de mensajes no leídos
        """
        return ChatMessage.query.filter(
            ChatMessage.receiver_id == user_id,
            ChatMessage.read_at.is_(None)
        ).count()
    
    def _notify_admins_new_ticket(self, ticket):
        """Notifica a administradores sobre nuevo ticket"""
        try:
            admins = User.query.filter_by(role='admin').all()
            for admin in admins:
                self.email_service.send_system_notification(
                    [admin.email],
                    'Nuevo Ticket de Soporte',
                    f'Se ha creado un nuevo ticket: {ticket.ticket_number}',
                    {
                        'ticket_number': ticket.ticket_number,
                        'title': ticket.title,
                        'category': ticket.category,
                        'priority': ticket.priority,
                        'user': ticket.user.username
                    }
                )
        except Exception as e:
            logger.error(f"Error al notificar admins sobre nuevo ticket: {str(e)}")
    
    def _notify_ticket_update(self, ticket, message):
        """Notifica sobre actualización de ticket"""
        try:
            # Notificar al creador del ticket
            if ticket.user_id != message.user_id:
                # El mensaje no fue enviado por el creador
                pass  # Implementar notificación
            
            # Notificar al asignado si existe
            if ticket.assigned_to and ticket.assigned_to != message.user_id:
                # El mensaje no fue enviado por el asignado
                pass  # Implementar notificación
                
        except Exception as e:
            logger.error(f"Error al notificar actualización de ticket: {str(e)}")
    
    def _notify_ticket_assignment(self, ticket, assignee):
        """Notifica sobre asignación de ticket"""
        try:
            # Implementar notificación por email
            pass
        except Exception as e:
            logger.error(f"Error al notificar asignación de ticket: {str(e)}")
    
    def _notify_status_change(self, ticket, old_status, new_status):
        """Notifica sobre cambio de estado"""
        try:
            # Implementar notificación por email
            pass
        except Exception as e:
            logger.error(f"Error al notificar cambio de estado: {str(e)}")