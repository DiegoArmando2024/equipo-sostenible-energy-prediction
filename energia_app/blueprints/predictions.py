# energia_app/blueprints/predictions.py
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime
import pandas as pd
from energia_app.forms import PredictionForm
from energia_app.models.user import Building, Prediction, db
from energia_app.models.model import Energy_Model
from energia_app.models.preprocess import preprocess_data

predictions_bp = Blueprint('predictions', __name__, url_prefix='/predict')

@predictions_bp.route('/', methods=['GET', 'POST'])
@login_required
def predict():
    active_buildings = Building.query.filter_by(active=True).all()
    form = PredictionForm()
    form.buildings.choices = [(b.id, b.name) for b in active_buildings]
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            selected_building_ids = form.buildings.data
            ocupacion = form.ocupacion.data
            dia_semana = form.dia_semana.data - 1
            hora_dia = form.hora_dia.data - 1
            
            selected_buildings = Building.query.filter(Building.id.in_(selected_building_ids)).all()
            model = Energy_Model()
            
            if not model.trained:
                flash('El modelo no está entrenado. Contacta al administrador.')
                return redirect(url_for('predictions.predict'))
            
            predictions = []
            total_consumption = 0
            
            for building in selected_buildings:
                input_data = pd.DataFrame({
                    'area_edificio': [building.area],
                    'ocupacion': [ocupacion],
                    'dia_semana': [dia_semana],
                    'hora_dia': [hora_dia]
                })
                
                X, _ = preprocess_data(input_data, training=False)
                prediction_value = round(float(model.predict(X)[0]), 2)
                
                new_prediction = Prediction(
                    building_id=building.id,
                    timestamp=datetime.now(),
                    ocupacion=ocupacion,
                    dia_semana=dia_semana,
                    hora_dia=hora_dia,
                    consumo_predicho=prediction_value
                )
                db.session.add(new_prediction)
                
                predictions.append({
                    'building_id': building.id,
                    'building_name': building.name,
                    'area': building.area,
                    'consumption': prediction_value,
                    'recommendations': generate_recommendations(building.area, ocupacion, dia_semana, hora_dia, prediction_value)
                })
                
                total_consumption += prediction_value
            
            db.session.commit()
            return render_template('predictions/predict.html', 
                                 form=form,
                                 buildings=active_buildings,
                                 predictions=predictions,
                                 total_consumption=round(total_consumption, 2),
                                 ocupacion=ocupacion,
                                 dia_semana=dia_semana,
                                 hora_dia=hora_dia)
        
        except Exception as e:
            flash(f'Error al procesar predicción: {str(e)}')
            return render_template('predictions/predict.html', form=form, buildings=active_buildings)
    
    # Return para GET requests
    return render_template('predictions/predict.html', form=form, buildings=active_buildings)

def generate_recommendations(area, ocupacion, dia_semana, hora_dia, prediction=None):
    """Función auxiliar para generar recomendaciones"""
    recommendations = []
    
    if dia_semana >= 5:
        recommendations.append("Programar apagado automático de sistemas no esenciales durante el fin de semana.")
    else:
        recommendations.append("Optimizar el encendido y apagado de equipos según horarios de mayor ocupación.")
    
    if 0 <= hora_dia < 6 or 22 <= hora_dia <= 23:
        recommendations.append("Implementar sensores de movimiento para iluminación en horario nocturno.")
    elif 8 <= hora_dia <= 18:
        recommendations.append("Establecer temperatura óptima de climatización según ocupación actual.")
    
    density = ocupacion / area * 100
    if density < 1:
        recommendations.append("Centralizar actividades en áreas específicas para reducir consumo en zonas desocupadas.")
    elif density > 3:
        recommendations.append("Mejorar la ventilación natural para reducir dependencia de sistemas de climatización.")
    
    recommendations.append("Realizar mantenimiento preventivo de equipos eléctricos para asegurar su eficiencia.")
    return recommendations[:3]