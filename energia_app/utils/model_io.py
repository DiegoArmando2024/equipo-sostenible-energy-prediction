"""
Módulo para cálculo de estadísticas y recomendaciones
Centraliza funciones comunes utilizadas en app.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.sql import extract, func

def get_building_stats(building, predictions=None):
    """
    Obtiene estadísticas para un edificio específico
    
    Args:
        building: Objeto Building
        predictions: Lista de predicciones (opcional, evita consulta adicional)
        
    Returns:
        dict: Estadísticas del edificio
    """
    stats = {
        'id': building.id,
        'name': building.name,
        'area': building.area,
        'location': building.location,
        'active': building.active
    }
    
    # Si se proporcionan predicciones, usarlas directamente
    if predictions is not None:
        building_predictions = [p for p in predictions if p.building_id == building.id]
    else:
        # De lo contrario, se asume que están disponibles a través de la relación
        building_predictions = building.predictions
    
    prediction_count = len(building_predictions)
    
    if prediction_count > 0:
        stats['avg_consumption'] = round(sum(p.consumo_predicho for p in building_predictions) / prediction_count, 2)
        stats['avg_occupancy'] = round(sum(p.ocupacion for p in building_predictions) / prediction_count, 1)
        stats['prediction_count'] = prediction_count
    else:
        stats.update({'avg_consumption': 0, 'avg_occupancy': 0, 'prediction_count': 0})
        
    return stats

def get_consumption_stats_by_period(db, Prediction, period_type='month', current_date=None):
    """
    Obtiene estadísticas de consumo para un período específico
    
    Args:
        db: Objeto SQLAlchemy database
        Prediction: Modelo de predicción
        period_type (str): Tipo de período ('month', 'year', 'week')
        current_date (datetime): Fecha actual (para pruebas)
        
    Returns:
        dict: Estadísticas de consumo
    """
    if current_date is None:
        current_date = datetime.now()
        
    # Configuración según período
    if period_type == 'month':
        current_period = current_date.month
        current_year = current_date.year
        previous_period = current_period - 1 if current_period > 1 else 12
        previous_year = current_year if current_period > 1 else current_year - 1
        days_in_period = 30
        period_name = current_date.strftime('%B %Y')
        extract_field = extract('month', Prediction.timestamp)
    elif period_type == 'year':
        current_period = current_date.year
        previous_period = current_period - 1
        previous_year = current_period - 1
        days_in_period = 365
        period_name = str(current_period)
        extract_field = extract('year', Prediction.timestamp)
    elif period_type == 'week':
        # Para semanas se requeriría más lógica específica
        # Esta es una implementación simplificada
        current_start = current_date - timedelta(days=current_date.weekday())
        previous_start = current_start - timedelta(days=7)
        days_in_period = 7
        period_name = f"Semana del {current_start.strftime('%d/%m/%Y')}"
        
        # En este caso no usamos extract sino rango de fechas
        current_predictions = Prediction.query.filter(
            Prediction.timestamp >= current_start,
            Prediction.timestamp < current_start + timedelta(days=7)
        ).all()
        
        previous_predictions = Prediction.query.filter(
            Prediction.timestamp >= previous_start,
            Prediction.timestamp < current_start
        ).all()
        
        # Cálculos directos sin SQL
        current_consumption = sum(p.consumo_predicho for p in current_predictions) / days_in_period if current_predictions else 0
        previous_consumption = sum(p.consumo_predicho for p in previous_predictions) / days_in_period if previous_predictions else 0
        
        # Calcular cambio porcentual
        if previous_consumption > 0:
            consumption_change = round((current_consumption - previous_consumption) / previous_consumption * 100, 1)
        else:
            consumption_change = 0
            
        return {
            'period_name': period_name,
            'total_consumption': round(current_consumption, 2),
            'consumption_change': consumption_change,
            'prediction_count': len(current_predictions)
        }
    
    # Para mes y año usamos SQL para consultas más eficientes
    
    # Obtener predicciones del período actual
    current_predictions = Prediction.query.filter(
        extract_field == current_period,
        extract('year', Prediction.timestamp) == current_year if current_year else True
    ).all()
    
    # Obtener predicciones del período anterior
    previous_predictions = Prediction.query.filter(
        extract_field == previous_period,
        extract('year', Prediction.timestamp) == previous_year if previous_year else True
    ).all()
    
    # Calcular consumo total
    if current_predictions:
        total_consumption = sum(p.consumo_predicho for p in current_predictions) / days_in_period
        total_consumption = round(total_consumption, 2)
    else:
        total_consumption = 0
    
    # Calcular cambio porcentual
    if previous_predictions:
        previous_consumption = sum(p.consumo_predicho for p in previous_predictions) / days_in_period
        if previous_consumption > 0:
            consumption_change = round((total_consumption - previous_consumption) / previous_consumption * 100, 1)
        else:
            consumption_change = 0
    else:
        consumption_change = 0
    
    return {
        'period_name': period_name,
        'total_consumption': total_consumption,
        'consumption_change': consumption_change,
        'prediction_count': len(current_predictions)
    }

def get_recommendations_by_category(area, ocupacion, dia_semana, hora_dia):
    """
    Obtiene recomendaciones categorizadas por tipo
    
    Args:
        area (float): Área del edificio
        ocupacion (int): Nivel de ocupación
        dia_semana (int): Día de la semana (0-6)
        hora_dia (int): Hora del día (0-23)
        
    Returns:
        dict: Recomendaciones por categoría
    """
    recommendations = {
        'tiempo': [],
        'ocupacion': [],
        'general': []
    }
    
    # Recomendaciones basadas en el día de la semana
    if dia_semana >= 5:  # Fin de semana
        recommendations['tiempo'].append(
            "Programar apagado automático de sistemas no esenciales durante el fin de semana."
        )
    else:  # Día laboral
        recommendations['tiempo'].append(
            "Optimizar el encendido y apagado de equipos según horarios de mayor ocupación."
        )
    
    # Recomendaciones basadas en la hora
    if 0 <= hora_dia < 6 or 22 <= hora_dia <= 23:  # Noche
        recommendations['tiempo'].append(
            "Implementar sensores de movimiento para iluminación en horario nocturno."
        )
    elif 8 <= hora_dia <= 18:  # Horario laboral
        recommendations['tiempo'].append(
            "Establecer temperatura óptima de climatización según ocupación actual."
        )
    
    # Recomendaciones basadas en la ocupación y área
    density = ocupacion / area * 100  # Personas por 100 m²
    if density < 1:
        recommendations['ocupacion'].append(
            "Centralizar actividades en áreas específicas para reducir consumo en zonas desocupadas."
        )
    elif density > 3:
        recommendations['ocupacion'].append(
            "Mejorar la ventilación natural para reducir dependencia de sistemas de climatización."
        )
    
    # Recomendación general de eficiencia energética
    recommendations['general'].append(
        "Realizar mantenimiento preventivo de equipos eléctricos para asegurar su eficiencia."
    )
    
    recommendations['general'].append(
        "Evaluar el reemplazo de equipos antiguos por alternativas de mayor eficiencia energética."
    )
    
    return recommendations

def generate_recommendations(area, ocupacion, dia_semana, hora_dia, prediction=None, limit=3):
    """
    Genera recomendaciones basadas en los parámetros de entrada
    
    Args:
        area (float): Área del edificio
        ocupacion (int): Nivel de ocupación
        dia_semana (int): Día de la semana (0-6)
        hora_dia (int): Hora del día (0-23)
        prediction (float, optional): Valor de la predicción
        limit (int): Número máximo de recomendaciones
        
    Returns:
        list: Lista de recomendaciones
    """
    all_recommendations = get_recommendations_by_category(area, ocupacion, dia_semana, hora_dia)
    
    # Aplanar todas las recomendaciones en una sola lista
    flat_recommendations = []
    # Priorizar categorías
    categories = ['tiempo', 'ocupacion', 'general']
    for category in categories:
        flat_recommendations.extend(all_recommendations[category])
    
    # Si se proporciona una predicción, podemos añadir recomendaciones específicas
    if prediction is not None:
        # Ejemplo: si la predicción es alta, añadir recomendación de ahorro
        if prediction > 100:  # Umbral ejemplo
            flat_recommendations.insert(0, "Considerar medidas inmediatas de reducción de consumo durante horas pico.")
    
    return flat_recommendations[:limit]