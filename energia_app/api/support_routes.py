from flask import Blueprint, request, jsonify, current_user
from flask_login import login_required
from energia_app.services.support_service import SupportService
from energia_app.models.support import SupportTicket, TicketMessage
import logging

logger = logging.getLogger(__name__)
support_bp = Blueprint('support_api', __name__, url_prefix='/api/support')

@support_bp.route('/tickets', methods=['GET'])
@login_required
def get_tickets():
    """Obtiene tickets del usuario actual"""
    try:
        page = request.args.get('page', 1, type=int)
        status_filter = request.args.get('status')
        
        support_service = SupportService()
        tickets_pagination = support_service.get_tickets_for_user(
            current_user.id, status_filter, page
        )
        
        return jsonify({
            'tickets': [ticket.to_dict() for ticket in tickets_pagination.items],
            'pagination': {
                'page': tickets_pagination.page,
                'pages': tickets_pagination.pages,
                'per_page': tickets_pagination.per_page,
                'total': tickets_pagination.total,
                'has_next': tickets_pagination.has_next,
                'has_prev': tickets_pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error al obtener tickets: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/tickets', methods=['POST'])
@login_required
def create_ticket():
    """Crea un nuevo ticket de soporte"""
    try:
        data = request.json
        
        # Validar datos requeridos
        required_fields = ['title', 'description', 'category']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        support_service = SupportService()
        ticket = support_service.create_ticket(
            user_id=current_user.id,
            title=data['title'],
            description=data['description'],
            category=data['category'],
            priority=data.get('priority', 'medium')
        )
        
        return jsonify({
            'message': 'Ticket creado exitosamente',
            'ticket': ticket.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error al crear ticket: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/tickets/<int:ticket_id>/messages', methods=['POST'])
@login_required
def add_message_to_ticket(ticket_id):
    """Añade un mensaje a un ticket"""
    try:
        data = request.json
        
        if 'message' not in data:
            return jsonify({'error': 'Campo requerido: message'}), 400
        
        support_service = SupportService()
        message = support_service.add_message_to_ticket(
            ticket_id=ticket_id,
            user_id=current_user.id,
            message=data['message'],
            is_internal=data.get('is_internal', False)
        )
        
        return jsonify({
            'message': 'Mensaje añadido exitosamente',
            'ticket_message': message.to_dict()
        })
        
    except PermissionError:
        return jsonify({'error': 'No tiene permisos para esta acción'}), 403
    except Exception as e:
        logger.error(f"Error al añadir mensaje: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/tickets/<int:ticket_id>/status', methods=['PUT'])
@login_required
def update_ticket_status(ticket_id):
    """Actualiza el estado de un ticket"""
    try:
        data = request.json
        
        if 'status' not in data:
            return jsonify({'error': 'Campo requerido: status'}), 400
        
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
        if data['status'] not in valid_statuses:
            return jsonify({'error': 'Estado inválido'}), 400
        
        support_service = SupportService()
        support_service.update_ticket_status(
            ticket_id=ticket_id,
            new_status=data['status'],
            user_id=current_user.id
        )
        
        return jsonify({'message': 'Estado actualizado exitosamente'})
        
    except PermissionError:
        return jsonify({'error': 'No tiene permisos para esta acción'}), 403
    except Exception as e:
        logger.error(f"Error al actualizar estado: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/chat/messages', methods=['POST'])
@login_required
def send_chat_message():
    """Envía un mensaje de chat"""
    try:
        data = request.json
        
        required_fields = ['receiver_id', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        support_service = SupportService()
        message = support_service.send_chat_message(
            sender_id=current_user.id,
            receiver_id=data['receiver_id'],
            message=data['message']
        )
        
        return jsonify({
            'message': 'Mensaje enviado exitosamente',
            'chat_message': message.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error al enviar mensaje de chat: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/chat/messages/<int:user_id>', methods=['GET'])
@login_required
def get_chat_messages(user_id):
    """Obtiene mensajes de chat con un usuario específico"""
    try:
        page = request.args.get('page', 1, type=int)
        
        support_service = SupportService()
        messages_pagination = support_service.get_chat_messages(
            current_user.id, user_id, page
        )
        
        return jsonify({
            'messages': [msg.to_dict() for msg in messages_pagination.items],
            'pagination': {
                'page': messages_pagination.page,
                'pages': messages_pagination.pages,
                'per_page': messages_pagination.per_page,
                'total': messages_pagination.total
            }
        })
        
    except Exception as e:
        logger.error(f"Error al obtener mensajes de chat: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@support_bp.route('/chat/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Obtiene el número de mensajes no leídos"""
    try:
        support_service = SupportService()
        count = support_service.get_unread_messages_count(current_user.id)
        
        return jsonify({'unread_count': count})
        
    except Exception as e:
        logger.error(f"Error al obtener mensajes no leídos: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500