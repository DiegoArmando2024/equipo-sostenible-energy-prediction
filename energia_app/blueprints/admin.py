from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from energia_app.models.user import User, db
from energia_app.models.energy_data import EnergyData
from energia_app.models.support import SupportTicket
from energia_app.forms import AdminUserForm
from energia_app.services import get_service
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def check_admin():
    """Verifica que el usuario sea admin antes de cada request"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('Acceso restringido a administradores', 'error')
        return redirect(url_for('dashboard.index'))

@admin_bp.route('/')
@login_required
def panel():
    """Panel de administración principal"""
    users = User.query.all()  # Agregar esta línea
    return render_template('admin/panel.html', users=users)

@admin_bp.route('/users')
@login_required
def manage_users():
    """Gestión de usuarios"""
    users = User.query.order_by(User.username).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Editar usuario"""
    user = User.query.get_or_404(user_id)
    form = AdminUserForm(obj=user)
    form._obj = user  # Establecer el usuario actual para validación
    
    if form.validate_on_submit():
        try:
            form.populate_obj(user)
            
            if form.password.data:
                user.set_password(form.password.data)
            
            db.session.commit()
            flash(f'Usuario {user.username} actualizado correctamente', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error actualizando usuario: {str(e)}")
            flash('Error al actualizar usuario', 'error')
    
    return render_template('admin/edit_user.html', form=form, user=user)

@admin_bp.route('/system-stats')
@login_required
def system_stats():
    """Estadísticas del sistema"""
    stats = {
        'users_count': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'energy_records': EnergyData.query.count(),
        'predictions_count': Prediction.query.count(),
        'open_tickets': SupportTicket.query.filter_by(status='open').count(),
        'active_buildings': Building.query.filter_by(active=True).count()
    }
    
    return render_template('admin/system_stats.html', stats=stats)

@admin_bp.route('/data-management')
@login_required
def data_management():
    """Gestión de datos del sistema"""
    return render_template('admin/data_management.html')

@admin_bp.route('/backup', methods=['POST'])
@login_required
def create_backup():
    """Crear respaldo del sistema"""
    try:
        backup_service = get_service('backup')
        backup_file = backup_service.create_backup()
        
        flash(f'Respaldo creado correctamente: {backup_file}', 'success')
        return redirect(url_for('admin.data_management'))
    
    except Exception as e:
        logging.error(f"Error creando respaldo: {str(e)}")
        flash('Error al crear respaldo', 'error')
        return redirect(url_for('admin.data_management'))