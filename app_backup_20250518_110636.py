from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import pandas as pd
import numpy as np
import logging
import io
import csv
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.sql import extract, func

# Importar modelos y utilidades
from energia_app.models import Energy_Model, preprocess_data
from energia_app.models.user import db, User, Building, Prediction
from energia_app.utils.data_loader import load_csv_dataset, save_dataset, get_dataset_statistics
from energia_app.forms import LoginForm, RegistrationForm, BuildingForm, PredictionForm , EnergyDataForm
from energia_app.models.energy_data import EnergyData


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
            template_folder='energia_app/templates',
            static_folder='energia_app/static')

# Configuración de la aplicación
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-predeterminada')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///energia_app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))



def ensure_model_trained():
    """Asegura que el modelo está entrenado con datos de la base de datos"""
    model = Energy_Model()
    
    # Si el modelo ya está entrenado, devolverlo
    if model.trained:
        return model
        
    # Verificar si existen datos en la base de datos
    energy_data_count = EnergyData.query.count()
    
    if energy_data_count < 100:  # Umbral mínimo de datos
        logger.error("No hay suficientes datos para entrenar el modelo")
        raise ValueError("No hay suficientes datos para entrenar el modelo. Por favor, añada al menos 100 registros de datos mediante importación o ingreso manual.")
    
    # Usar datos de la base de datos para entrenar
    try:
        logger.info(f"Usando {energy_data_count} registros de la base de datos para entrenar el modelo")
        data_df = EnergyData.export_to_df()
        X, y = preprocess_data(data_df, training=True)
        metrics = model.train(X, y)
        logger.info(f"Modelo entrenado con éxito. Métricas: R² = {metrics['r2']:.4f}")
        return model
    except Exception as e:
        logger.error(f"Error al entrenar el modelo: {str(e)}")
        raise

def generate_recommendations(area, ocupacion, dia_semana, hora_dia, prediction=None):
    """
    Genera recomendaciones basadas en los parámetros de entrada
    
    Args:
        area (float): Área del edificio
        ocupacion (int): Nivel de ocupación
        dia_semana (int): Día de la semana (0-6)
        hora_dia (int): Hora del día (0-23)
        prediction (float, optional): Predicción de consumo
        
    Returns:
        list: Lista de hasta 3 recomendaciones
    """
    recommendations = []
    
    # Recomendaciones basadas en el día de la semana
    if dia_semana >= 5:  # Fin de semana
        recommendations.append("Programar apagado automático de sistemas no esenciales durante el fin de semana.")
    else:  # Día laboral
        recommendations.append("Optimizar el encendido y apagado de equipos según horarios de mayor ocupación.")
    
    # Recomendaciones basadas en la hora
    if 0 <= hora_dia < 6 or 22 <= hora_dia <= 23:  # Noche
        recommendations.append("Implementar sensores de movimiento para iluminación en horario nocturno.")
    elif 8 <= hora_dia <= 18:  # Horario laboral
        recommendations.append("Establecer temperatura óptima de climatización según ocupación actual.")
    
    # Recomendaciones basadas en la ocupación y área
    density = ocupacion / area * 100  # Personas por 100 m²
    if density < 1:
        recommendations.append("Centralizar actividades en áreas específicas para reducir consumo en zonas desocupadas.")
    elif density > 3:
        recommendations.append("Mejorar la ventilación natural para reducir dependencia de sistemas de climatización.")
    
    # Recomendación general de eficiencia energética
    recommendations.append("Realizar mantenimiento preventivo de equipos eléctricos para asegurar su eficiencia.")
    
    return recommendations[:3]  # Limitamos a 3 recomendaciones

def get_building_stats(building, predictions=None):
    """
    Obtiene estadísticas para un edificio específico
    
    Args:
        building: Objeto Building
        predictions: Lista de predicciones (opcional)
        
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
    
    # Si se proporcionan predicciones, usar esas
    if predictions is not None:
        building_predictions = [p for p in predictions if p.building_id == building.id]
    else:
        building_predictions = Prediction.query.filter_by(building_id=building.id).all()
    
    prediction_count = len(building_predictions)
    
    if prediction_count > 0:
        stats['avg_consumption'] = round(sum(p.consumo_predicho for p in building_predictions) / prediction_count, 2)
        stats['avg_occupancy'] = round(sum(p.ocupacion for p in building_predictions) / prediction_count, 1)
        stats['prediction_count'] = prediction_count
    else:
        stats.update({'avg_consumption': 0, 'avg_occupancy': 0, 'prediction_count': 0})
        
    return stats

# Crear tablas de la base de datos
with app.app_context():
    db.create_all()
    
    # Crear usuario administrador si no existe
    admin = User.query.filter_by(username='admin').first()
    if admin is None:
        admin_password = os.environ.get('ADMIN_PASSWORD', 'adminpassword')
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        logger.info("Usuario administrador creado con éxito.")

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña inválidos')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # Asegurar que next_page es relativo a nuestro sitio
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Rutas para gestión de edificios
# Rutas para gestión de edificios
@app.route('/buildings', methods=['GET', 'POST'])  # Asegúrate de que incluya POST
@app.route('/buildings/<int:building_id>', methods=['GET'])
@login_required
def manage_buildings(building_id=None):
    """Gestión de edificios para predicciones"""
    # Inicializar formulario
    form = BuildingForm()
    
    # Si se está editando, cargar datos del edificio
    if building_id:
        building = Building.query.get_or_404(building_id)
        if request.method == 'GET':
            form.id.data = building.id
            form.name.data = building.name
            form.area.data = building.area
            form.location.data = building.location
            form.description.data = building.description
            form.active.data = building.active
    
    # Procesar formulario si se envía
    if form.validate_on_submit():
        if form.id.data and int(form.id.data) > 0:  # Edición
            building = Building.query.get_or_404(int(form.id.data))
            building.name = form.name.data
            building.area = form.area.data
            building.location = form.location.data
            building.description = form.description.data
            building.active = form.active.data
            db.session.commit()
            flash(f'Edificio "{building.name}" actualizado correctamente.')
            return redirect(url_for('manage_buildings'))
        else:  # Creación
            new_building = Building(
                name=form.name.data,
                area=form.area.data,
                location=form.location.data,
                description=form.description.data,
                active=form.active.data
            )
            db.session.add(new_building)
            db.session.commit()
            flash(f'Edificio "{new_building.name}" registrado correctamente.')
            return redirect(url_for('manage_buildings'))
    
    # Obtener todos los edificios para mostrar en la lista
    buildings = Building.query.order_by(Building.name).all()
    
    return render_template('buildings.html', form=form, buildings=buildings)

@app.route('/buildings/delete/<int:building_id>')
@login_required
def delete_building(building_id):
    """Eliminar un edificio"""
    if current_user.role != 'admin':
        flash('No tienes permisos para eliminar edificios.')
        return redirect(url_for('manage_buildings'))
    
    building = Building.query.get_or_404(building_id)
    name = building.name
    
    # Verificar si hay predicciones asociadas
    predicciones = Prediction.query.filter_by(building_id=building_id).count()
    if predicciones > 0:
        flash(f'No se puede eliminar el edificio "{name}" porque tiene predicciones asociadas.')
        return redirect(url_for('manage_buildings'))
    
    db.session.delete(building)
    db.session.commit()
    flash(f'Edificio "{name}" eliminado correctamente.')
    
    return redirect(url_for('manage_buildings'))

# Actualizar la ruta de predicción para usar edificios
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    # Obtener edificios activos para el formulario
    active_buildings = Building.query.filter_by(active=True).all()
    
    # Crear formulario con opciones dinámicas de edificios
    form = PredictionForm()
    form.buildings.choices = [(b.id, b.name) for b in active_buildings]
    
    if request.method == 'POST' and form.validate_on_submit():
        # Obtener parámetros del formulario
        selected_building_ids = form.buildings.data
        ocupacion = form.ocupacion.data
        dia_semana = form.dia_semana.data
        hora_dia = form.hora_dia.data
        
        # Verificar que se seleccionaron edificios
        if not selected_building_ids:
            flash('Por favor, seleccione al menos un edificio.')
            return render_template('prediction.html', form=form, buildings=active_buildings)
        
        # Obtener los edificios seleccionados
        selected_buildings = Building.query.filter(Building.id.in_(selected_building_ids)).all()
        
        # Asegurar que el modelo está entrenado
        try:
            model = ensure_model_trained()
        except ValueError as e:
            flash(str(e))
            return render_template('prediction.html', form=form, buildings=active_buildings)
        
        # Realizar predicciones para cada edificio
        predictions = []
        total_consumption = 0
        
        for building in selected_buildings:
            # Crear DataFrame con los datos de entrada
            input_data = pd.DataFrame({
                'area_edificio': [building.area],
                'ocupacion': [ocupacion],
                'dia_semana': [dia_semana],
                'hora_dia': [hora_dia]
            })
            
            try:
                # Preprocesar datos de entrada
                X, _ = preprocess_data(input_data, training=False)
                
                # Realizar predicción
                prediction_value = model.predict(X)[0]
                
                # Redondear predicción a 2 decimales
                prediction_value = round(float(prediction_value), 2)
                
                # Generar recomendaciones para este edificio
                recommendations = generate_recommendations(building.area, ocupacion, dia_semana, hora_dia, prediction_value)
                
                # Guardar la predicción en la base de datos
                new_prediction = Prediction(
                    building_id=building.id,
                    timestamp=datetime.now(),
                    ocupacion=ocupacion,
                    dia_semana=dia_semana,
                    hora_dia=hora_dia,
                    consumo_predicho=prediction_value
                )
                db.session.add(new_prediction)
                
                # Añadir a la lista de predicciones
                predictions.append({
                    'building_id': building.id,
                    'building_name': building.name,
                    'area': building.area,
                    'consumption': prediction_value,
                    'recommendations': recommendations
                })
                
                # Acumular consumo total
                total_consumption += prediction_value
                
            except Exception as e:
                logger.error(f"Error al realizar predicción para edificio {building.name}: {str(e)}")
                flash(f'Error al procesar predicción para {building.name}: {str(e)}')
        
        # Guardar cambios en la base de datos
        db.session.commit()
        
        # Redondear consumo total
        total_consumption = round(total_consumption, 2)
        
        # Renderizar template con resultados
        return render_template('prediction.html', 
                              form=form,
                              buildings=active_buildings,
                              predictions=predictions,
                              total_consumption=total_consumption,
                              ocupacion=ocupacion,
                              dia_semana=dia_semana,
                              hora_dia=hora_dia)
    
    # Si es GET, mostrar formulario
    return render_template('prediction.html', form=form, buildings=active_buildings)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/data')
@login_required
def get_data():
    """API para obtener datos para las gráficas del dashboard, directamente desde la base de datos"""
    try:
        # Verificar si existen datos en la base de datos
        total_records = EnergyData.query.count()
        
        if total_records == 0:
            return jsonify({'error': 'No hay datos suficientes para generar gráficas. Por favor, añada algunos datos primero.'}), 404
        
        # Obtener datos desde la base de datos
        data_df = EnergyData.export_to_df()
        
        # Datos de consumo por hora
        consumo_horas = {
            'horas': list(range(24)),
            'consumo': []
        }
        
        for h in range(24):
            hora_data = data_df[data_df['hora_dia'] == h]
            if not hora_data.empty:
                consumo_horas['consumo'].append(round(hora_data['consumo_energetico'].mean(), 2))
            else:
                consumo_horas['consumo'].append(0)
        
        # Datos de consumo por día
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        consumo_dias = {
            'dias': dias_semana,
            'consumo': []
        }
        
        for d in range(7):
            dia_data = data_df[data_df['dia_semana'] == d]
            if not dia_data.empty:
                consumo_dias['consumo'].append(round(dia_data['consumo_energetico'].mean(), 2))
            else:
                consumo_dias['consumo'].append(0)
        
        # Datos de consumo por edificio usando datos reales de edificios
        edificios_reales = Building.query.all()
        
        if edificios_reales:
            # Usar edificios reales de la base de datos
            edificios = [b.name for b in edificios_reales]
            consumo_edificios = {
                'edificios': edificios,
                'consumo': []
            }
            
            # Obtener consumo promedio de edificios
            for building in edificios_reales:
                # Primero buscar registros asociados directamente al edificio
                edificio_data = EnergyData.query.filter_by(building_id=building.id).all()
                
                if edificio_data:
                    # Si hay datos directos, usar el promedio
                    consumo_medio = sum(data.consumo_energetico for data in edificio_data) / len(edificio_data)
                    consumo_edificios['consumo'].append(round(consumo_medio, 2))
                else:
                    # Buscar datos por área similar
                    area = building.area
                    area_min = area * 0.9
                    area_max = area * 1.1
                    area_data = data_df[(data_df['area_edificio'] >= area_min) & 
                                      (data_df['area_edificio'] <= area_max)]
                    
                    if not area_data.empty:
                        consumo_medio = area_data['consumo_energetico'].mean()
                        consumo_edificios['consumo'].append(round(consumo_medio, 2))
                    else:
                        # Si no hay datos para este edificio, usar promedio general
                        consumo_edificios['consumo'].append(round(data_df['consumo_energetico'].mean(), 2))
        else:
            # Si no hay edificios, agrupar por rango de áreas
            areas_edificios = [1000, 2000, 3000, 4000, 5000]
            edificios = ['Área ~1000m²', 'Área ~2000m²', 'Área ~3000m²', 'Área ~4000m²', 'Área ~5000m²']
            
            consumo_edificios = {
                'edificios': edificios,
                'consumo': []
            }
            
            # Para cada rango de área, calcular el consumo promedio
            for area in areas_edificios:
                area_min = area * 0.8
                area_max = area * 1.2
                
                area_data = data_df[(data_df['area_edificio'] >= area_min) & 
                                  (data_df['area_edificio'] <= area_max)]
                
                if not area_data.empty:
                    consumo_medio = area_data['consumo_energetico'].mean()
                    consumo_edificios['consumo'].append(round(consumo_medio, 2))
                else:
                    # Si no hay datos para este rango, usar promedio general
                    consumo_edificios['consumo'].append(round(data_df['consumo_energetico'].mean(), 2))
        
        return jsonify({
            'consumo_horas': consumo_horas,
            'consumo_dias': consumo_dias,
            'consumo_edificios': consumo_edificios
        })
    
    except Exception as e:
        logger.error(f"Error al generar datos para dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

@app.route('/download/<filename>')
@login_required
def download_file(filename):
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('index'))
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rutas de administración
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

    
@app.route('/buildings/dashboard')
@login_required
def buildings_dashboard():
    """Dashboard de estadísticas de edificios"""
    try:
        # Obtener todos los edificios
        buildings = Building.query.all()
        active_buildings = Building.query.filter_by(active=True).all()
        
        # Calcular área total
        total_area = sum(building.area for building in buildings)
        total_area = round(total_area, 2)
        
        # Estadísticas de predicciones
        total_predictions = Prediction.query.count()
        
        # Predicciones recientes (último mes)
        recent_predictions = Prediction.query.filter(
            Prediction.timestamp >= datetime.now() - timedelta(days=30)
        ).count()
        
        # Promedio de predicciones por día
        if recent_predictions > 0:
            avg_predictions_per_day = round(recent_predictions / 30, 1)
        else:
            avg_predictions_per_day = 0
        
        # Consumo total estimado
        current_month = datetime.now().month
        current_year = datetime.now().year
        current_month_year = datetime.now().strftime('%B %Y')
        
        # Obtener predicciones del mes actual (usando SQL nativo para optimizar)
        current_month_predictions = db.session.query(
            func.sum(Prediction.consumo_predicho).label('total_consumo')
        ).filter(
            extract('month', Prediction.timestamp) == current_month,
            extract('year', Prediction.timestamp) == current_year
        ).scalar()
        
        # Calcular consumo total
        if current_month_predictions:
            total_consumption = round(float(current_month_predictions) / 30, 2)
        else:
            total_consumption = 0
        
        # Calcular cambio porcentual respecto al mes anterior
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_consumption = db.session.query(
            func.sum(Prediction.consumo_predicho).label('total_consumo')
        ).filter(
            extract('month', Prediction.timestamp) == last_month,
            extract('year', Prediction.timestamp) == last_month_year
        ).scalar()
        
        if last_month_consumption:
            last_month_consumption = float(last_month_consumption) / 30
            if last_month_consumption > 0:
                consumption_change = round((total_consumption - last_month_consumption) / last_month_consumption * 100, 1)
            else:
                consumption_change = 0
        else:
            consumption_change = 0
        
        # Obtener todas las predicciones en una sola consulta
        all_predictions = Prediction.query.all()
        
        # Detalles de cada edificio
        buildings_details = []
        for building in buildings:
            # Usar la función helper para obtener estadísticas del edificio
            stats = get_building_stats(building, all_predictions)
            buildings_details.append(stats)
        
        return render_template(
            'buildings_dashboard.html',
            buildings=buildings,
            active_buildings=active_buildings,
            total_area=total_area,
            total_predictions=total_predictions,
            recent_predictions=recent_predictions,
            avg_predictions_per_day=avg_predictions_per_day,
            total_consumption=total_consumption,
            consumption_change=consumption_change,
            current_month_year=current_month_year,
            buildings_details=buildings_details
        )
    
    except Exception as e:
        logger.error(f"Error al generar dashboard de edificios: {str(e)}")
        flash(f'Error al generar dashboard: {str(e)}')
        return redirect(url_for('manage_buildings'))
    

@app.route('/data-management')
@login_required
def data_management():
    """Página principal para gestión de datos"""
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.')
        return redirect(url_for('index'))
    
    # Crear formulario para ingreso manual
    manual_form = EnergyDataForm()
    
    # Cargar opciones de edificios para el formulario
    buildings = Building.query.filter_by(active=True).all()
    manual_form.building_id.choices = [(0, 'Seleccione un edificio (opcional)')] + [(b.id, b.name) for b in buildings]
    
    # Obtener datos recientes para mostrar
    energy_data = EnergyData.query.order_by(EnergyData.timestamp.desc()).limit(10).all()
    
    # Obtener estadísticas de los datos en la base de datos
    dataset_stats = None
    total_manual_records = EnergyData.query.count()
    
    # Si hay suficientes datos, obtener estadísticas
    if total_manual_records > 0:
        try:
            # Exportar datos para estadísticas
            data_df = EnergyData.export_to_df()
            
            # Obtener estadísticas básicas
            dataset_stats = {
                'n_samples': len(data_df),
                'area_min': data_df['area_edificio'].min(),
                'area_max': data_df['area_edificio'].max(),
                'consumo_min': data_df['consumo_energetico'].min(),
                'consumo_max': data_df['consumo_energetico'].max(),
                'consumo_mean': data_df['consumo_energetico'].mean()
            }
            
            # Calcular correlaciones si hay suficientes datos
            if len(data_df) >= 10:
                correlaciones = {
                    'area_consumo': data_df['area_edificio'].corr(data_df['consumo_energetico']),
                    'ocupacion_consumo': data_df['ocupacion'].corr(data_df['consumo_energetico']),
                    'dia_consumo': data_df['dia_semana'].corr(data_df['consumo_energetico']),
                    'hora_consumo': data_df['hora_dia'].corr(data_df['consumo_energetico'])
                }
                dataset_stats['correlaciones'] = correlaciones
        except Exception as e:
            logger.error(f"Error al calcular estadísticas: {str(e)}")
    
    # Preparar datos de edificios para el script de autocompletado
    buildings_data = [{
        'id': b.id,
        'name': b.name,
        'area': b.area
    } for b in buildings]
    
    # Procesar el formulario de ingreso manual si se envía
    if request.method == 'POST' and manual_form.validate_on_submit():
        try:
            # Crear nuevo registro
            new_data = EnergyData(
                area_edificio=manual_form.area_edificio.data,
                ocupacion=manual_form.ocupacion.data,
                dia_semana=manual_form.dia_semana.data,
                hora_dia=manual_form.hora_dia.data,
                consumo_energetico=manual_form.consumo_energetico.data
            )
            
            # Asignar edificio si se seleccionó
            if manual_form.building_id.data and manual_form.building_id.data > 0:
                new_data.building_id = manual_form.building_id.data
            
            # Guardar en la base de datos
            db.session.add(new_data)
            db.session.commit()
            
            flash('Registro guardado correctamente.')
            return redirect(url_for('data_management'))
        except Exception as e:
            flash(f'Error al guardar el registro: {str(e)}')
    
    return render_template(
        'data_management.html',
        manual_form=manual_form,
        energy_data=energy_data,
        dataset_stats=dataset_stats,
        total_manual_records=total_manual_records,
        buildings_data=buildings_data
    )

@app.route('/retrain', methods=['POST'])
@login_required
def retrain_model():
    """Reentrenar el modelo con todos los datos de la base de datos"""
    if current_user.role != 'admin':
        flash('No tienes permisos para realizar esta acción.')
        return redirect(url_for('index'))
    
    try:
        # Verificar si hay suficientes datos
        total_records = EnergyData.query.count()
        
        if total_records < 100:  # Umbral mínimo
            flash('No hay suficientes datos para entrenar el modelo. Se requieren al menos 100 registros.')
            return redirect(url_for('data_management'))
        
        # Obtener todos los datos de la base de datos
        data_df = EnergyData.export_to_df()
        
        # Preprocesar datos
        X, y = preprocess_data(data_df, training=True)
        
        # Inicializar y entrenar el modelo
        model = Energy_Model()
        metrics = model.train(X, y)
        
        flash(f'Modelo reentrenado con éxito. Métricas: R² = {metrics["r2"]:.4f}, RMSE = {metrics["rmse"]:.4f}')
        return redirect(url_for('data_management'))
    
    except Exception as e:
        logger.error(f"Error al reentrenar el modelo: {str(e)}")
        flash(f'Error al reentrenar el modelo: {str(e)}')
        return redirect(url_for('data_management'))

@app.route('/manual-data')
@login_required
def manual_data():
    """Redirección a la página de gestión de datos (pestaña manual)"""
    return redirect(url_for('data_management') + '#manual')

@app.route('/data-management/upload-energy-data', methods=['POST'])
@login_required
def upload_energy_data():
    """Importa datos desde un archivo CSV directamente a la base de datos"""
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('No se ha seleccionado ningún archivo')
        return redirect(url_for('data_management'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No se ha seleccionado ningún archivo')
        return redirect(url_for('data_management'))
    
    if file and allowed_file(file.filename):
        try:
            # Leer CSV
            data = pd.read_csv(file)
            
            # Validar columnas requeridas
            required_cols = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                flash(f'El archivo CSV no tiene las columnas requeridas: {", ".join(missing_cols)}')
                return redirect(url_for('data_management'))
            
            # Importar como registros individuales
            count = EnergyData.import_from_df(data)
            flash(f'Se han importado {count} registros correctamente a la base de datos.')
            
            # Reentrenar modelo si se solicitó
            if 'retrain' in request.form and request.form['retrain'] == 'yes':
                try:
                    # Utilizar todos los datos de la base de datos para entrenar
                    all_data = EnergyData.export_to_df()
                    X, y = preprocess_data(all_data, training=True)
                    
                    # Entrenar modelo
                    model = Energy_Model()
                    metrics = model.train(X, y)
                    
                    flash(f'Modelo reentrenado con éxito. R² = {metrics["r2"]:.4f}')
                except Exception as e:
                    flash(f'Error al reentrenar el modelo: {str(e)}')
            
            return redirect(url_for('data_management') + '#data-import')
            
        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}')
            return redirect(url_for('data_management'))
    else:
        flash('Tipo de archivo no permitido. Por favor, sube un archivo CSV.')
        return redirect(url_for('data_management'))

@app.route('/export-energy-data')
@login_required
def export_energy_data():
    """Exporta los datos de consumo energético a CSV"""
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('index'))
    
    # Obtener todos los registros
    energy_data = EnergyData.query.all()
    
    # Crear CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow(['id', 'timestamp', 'building_id', 'area_edificio', 'ocupacion', 
                     'dia_semana', 'hora_dia', 'consumo_energetico'])
    
    # Escribir datos
    for data in energy_data:
        writer.writerow([
            data.id,
            data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            data.building_id,
            data.area_edificio,
            data.ocupacion,
            data.dia_semana,
            data.hora_dia,
            data.consumo_energetico
        ])
    
    # Preparar respuesta
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=energy_data.csv"}
    )

@app.route('/delete-all-energy-data')
@login_required
def delete_all_energy_data():
    """Elimina todos los registros de datos energéticos"""
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('index'))
    
    try:
        # Eliminar todos los registros
        EnergyData.query.delete()
        db.session.commit()
        flash('Todos los registros de datos energéticos han sido eliminados.')
    except Exception as e:
        flash(f'Error al eliminar los registros: {str(e)}')
    
    return redirect(url_for('data_management'))

if __name__ == '__main__':
    app.run(debug=True)