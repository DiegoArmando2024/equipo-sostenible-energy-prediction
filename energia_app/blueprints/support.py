from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from energia_app.models.support import SupportTicket, TicketMessage, ChatMessage
from energia_app.models.user import User
from energia_app.forms import SupportTicketForm, TicketMessageForm
from energia_app.services import get_service
import logging

support_bp = Blueprint('support', __name__, url_prefix='/support')

@support_bp.route('/')
@login_required
def index():
    """Página principal de soporte"""
    return render_template('support/index.html')

@support_bp.route('/tickets')
@login_required
def tickets():
    """Lista de tickets del usuario"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    
    support_service = get_service('support')
    tickets_pagination = support_service.get_tickets_for_user(
        current_user.id, status_filter, page
    )
    
    return render_template('support/tickets.html', 
                         tickets=tickets_pagination.items,
                         pagination=tickets_pagination,
                         status_filter=status_filter)

@support_bp.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """Crear nuevo ticket de soporte"""
    form = SupportTicketForm()
    
    if form.validate_on_submit():
        try:
            support_service = get_service('support')
            ticket = support_service.create_ticket(
                user_id=current_user.id,
                title=form.title.data,
                description=form.description.data,
                category=form.category.data,
                priority=form.priority.data
            )
            
            flash('Ticket creado exitosamente', 'success')
            return redirect(url_for('support.ticket_detail', ticket_id=ticket.id))
        except Exception as e:
            logging.error(f"Error creando ticket: {str(e)}")
            flash('Error al crear ticket', 'error')
    
    return render_template('support/new_ticket.html', form=form)

@support_bp.route('/tickets/<int:ticket_id>')
@login_required
def ticket_detail(ticket_id):
    """Detalle de un ticket"""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Verificar permisos
    if not ticket.can_be_edited_by(current_user):
        flash('No tienes permisos para ver este ticket', 'error')
        return redirect(url_for('support.tickets'))
    
    form = TicketMessageForm()
    return render_template('support/ticket_detail.html', 
                         ticket=ticket, 
                         form=form)

@support_bp.route('/tickets/<int:ticket_id>/messages', methods=['POST'])
@login_required
def add_message(ticket_id):
    """Añadir mensaje a un ticket"""
    ticket = SupportTicket.query.get_or_404(ticket_id)
    form = TicketMessageForm()
    
    if not ticket.can_be_edited_by(current_user):
        flash('No tienes permisos para este ticket', 'error')
        return redirect(url_for('support.tickets'))
    
    if form.validate_on_submit():
        try:
            support_service = get_service('support')
            support_service.add_message_to_ticket(
                ticket_id=ticket.id,
                user_id=current_user.id,
                message=form.message.data,
                is_internal=form.is_internal.data
            )
            
            flash('Mensaje añadido correctamente', 'success')
        except Exception as e:
            logging.error(f"Error añadiendo mensaje: {str(e)}")
            flash('Error al añadir mensaje', 'error')
    
    return redirect(url_for('support.ticket_detail', ticket_id=ticket.id))

@support_bp.route('/chat')
@login_required
def chat():
    """Interfaz de chat"""
    # Obtener conversaciones recientes
    conversations = ChatMessage.query.filter(
        (ChatMessage.sender_id == current_user.id) |
        (ChatMessage.receiver_id == current_user.id)
    ).order_by(ChatMessage.created_at.desc()).all()
    
    # Procesar para mostrar lista de contactos
    contacts = {}
    for msg in conversations:
        other_user_id = msg.sender_id if msg.sender_id != current_user.id else msg.receiver_id
        if other_user_id not in contacts:
            user = User.query.get(other_user_id)
            contacts[other_user_id] = {
                'user': user,
                'last_message': msg.created_at,
                'unread': msg.receiver_id == current_user.id and not msg.read_at
            }
    
    # Ordenar por último mensaje
    sorted_contacts = sorted(contacts.values(), key=lambda x: x['last_message'], reverse=True)
    
    return render_template('support/chat.html', contacts=sorted_contacts)

@support_bp.route('/chat/<int:user_id>')
@login_required
def chat_conversation(user_id):
    """Conversación de chat con un usuario específico"""
    other_user = User.query.get_or_404(user_id)
    
    page = request.args.get('page', 1, type=int)
    messages = ChatMessage.query.filter(
        ((ChatMessage.sender_id == current_user.id) & 
         (ChatMessage.receiver_id == user_id)) |
        ((ChatMessage.sender_id == user_id) & 
         (ChatMessage.receiver_id == current_user.id))
    ).order_by(ChatMessage.created_at.desc()).paginate(page=page, per_page=20)
    
    # Marcar mensajes como leídos
    support_service = get_service('support')
    support_service.mark_messages_as_read(current_user.id, user_id)
    
    return render_template('support/chat_conversation.html', 
                         other_user=other_user,
                         messages=messages)