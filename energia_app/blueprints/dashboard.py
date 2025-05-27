from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from energia_app.models.user import User, Building, Prediction
from energia_app.models.energy_data import EnergyData
from energia_app.services import get_service
import logging
import pandas as pd

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Página principal del dashboard"""
    try:
        # Obtener estadísticas generales
        total_buildings = Building.query.count()
        total_predictions = Prediction.query.count()
        total_users = User.query.count()
        
        # Intentar obtener total de registros de energía
        total_records = 0
        try:
            total_records = EnergyData.query.count()
        except:
            # Si EnergyData no existe, usar 0
            total_records = 0
        
        # Obtener predicciones recientes
        recent_predictions = Prediction.query.order_by(Prediction.timestamp.desc()).limit(5).all()
        
        return render_template('dashboard/index.html',
                             total_buildings=total_buildings,
                             total_predictions=total_predictions,
                             total_records=total_records,
                             total_users=total_users,
                             recent_predictions=recent_predictions)
    except Exception as e:
        logging.error(f"Error en dashboard: {str(e)}")
        # En caso de error, pasar valores por defecto
        return render_template('dashboard/index.html',
                             total_buildings=0,
                             total_predictions=0,
                             total_records=0,
                             total_users=0,
                             recent_predictions=[])

@dashboard_bp.route('/api/consumption-data')
@login_required
def consumption_data():
    """API para datos de consumo del dashboard"""
    try:
        # Obtener datos desde la base de datos
        data_df = EnergyData.export_to_df()
        
        if data_df.empty:
            return jsonify({'error': 'No hay datos disponibles'}), 404
        
        # Datos de consumo por hora
        consumo_horas = {
            'horas': list(range(24)),
            'consumo': []
        }
        
        for h in range(24):
            hora_data = data_df[data_df['hora_dia'] == h]
            consumo_horas['consumo'].append(
                round(hora_data['consumo_energetico'].mean(), 2) if not hora_data.empty else 0
        )
        
        # Datos de consumo por día
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        consumo_dias = {
            'dias': dias_semana,
            'consumo': []
        }
        
        for d in range(7):
            dia_data = data_df[data_df['dia_semana'] == d]
            consumo_dias['consumo'].append(
                round(dia_data['consumo_energetico'].mean(), 2) if not dia_data.empty else 0
            )
        
        # Datos de consumo por edificio
        buildings = Building.query.all()
        consumo_edificios = {
            'edificios': [b.name for b in buildings],
            'consumo': []
        }
        
        for building in buildings:
            building_data = data_df[data_df['building_id'] == building.id]
            consumo_edificios['consumo'].append(
                round(building_data['consumo_energetico'].mean(), 2) if not building_data.empty else 0
            )
        
        return jsonify({
            'consumo_horas': consumo_horas,
            'consumo_dias': consumo_dias,
            'consumo_edificios': consumo_edificios
        })
    
    except Exception as e:
        logging.error(f"Error en dashboard API: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@dashboard_bp.route('/api/user-stats')
@login_required
def user_stats():
    """Estadísticas del usuario actual"""
    try:
        # Predicciones recientes del usuario
        predictions = Prediction.query.order_by(Prediction.timestamp.desc()).limit(5).all()
        
        # Edificios activos
        buildings = Building.query.filter_by(active=True).all()
        
        return jsonify({
            'user': {
                'username': current_user.username,
                'email': current_user.email,
                'role': current_user.role
            },
            'recent_predictions': [
                {
                    'id': p.id,
                    'building': p.building.name if p.building else 'N/A',
                    'consumption': p.consumo_predicho,
                    'timestamp': p.timestamp.strftime('%Y-%m-%d %H:%M')
                } for p in predictions
            ],
            'buildings': [
                {
                    'id': b.id,
                    'name': b.name,
                    'area': b.area
                } for b in buildings
            ],
            'prediction_count': Prediction.query.count()
        })
        
    except Exception as e:
        logging.error(f"Error obteniendo stats de usuario: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500