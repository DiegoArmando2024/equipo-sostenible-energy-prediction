from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import pandas as pd
import numpy as np
import logging
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from sqlalchemy.sql import extract, func

# Importar modelos y utilidades
from energia_app.models import Energy_Model, preprocess_data
from energia_app.models.user import db, User, Building, Prediction  # Importación correcta de Building y Prediction
from energia_app.utils import generate_synthetic_data, generate_future_scenarios
from energia_app.utils.data_loader import load_csv_dataset, save_dataset, get_dataset_statistics
from energia_app.forms import LoginForm, RegistrationForm, BuildingForm, PredictionForm 



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
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max-limit
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




def allowed_file(filename):
    """Verifica si la extensión del archivo es permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Asegurar que el modelo está entrenado
def ensure_model_trained():
    model = Energy_Model()
    
    # Ruta de datos predeterminada
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
    os.makedirs(data_dir, exist_ok=True)
    data_path = os.path.join(data_dir, 'energy_data.csv')
    
    # Si el modelo no está entrenado, comprobamos si existe un dataset
    if not model.trained:
        logger.info("Modelo no entrenado. Buscando dataset para entrenar...")
        
        if os.path.exists(data_path):
            logger.info(f"Dataset encontrado en {data_path}. Cargando datos...")
            # Cargar dataset existente
            try:
                data = load_csv_dataset(data_path)
                logger.info(f"Dataset cargado con {len(data)} registros.")
            except Exception as e:
                logger.error(f"Error al cargar dataset: {str(e)}. Generando datos sintéticos...")
                data = generate_synthetic_data(n_samples=1000)
                data.to_csv(data_path, index=False)
        else:
            logger.info("No se encontró dataset. Generando datos sintéticos...")
            data = generate_synthetic_data(n_samples=1000)
            # Guardar los datos para referencia futura
            data.to_csv(data_path, index=False)
        
        # Preprocesar datos
        X, y = preprocess_data(data, training=True)
        
        # Entrenar modelo
        metrics = model.train(X, y)
        logger.info(f"Modelo entrenado con éxito. Métricas: R² = {metrics['r2']:.4f}")
    
    return model

# Función para generar recomendaciones basadas en los parámetros de entrada
def generate_recommendations(area, ocupacion, dia_semana, hora_dia, prediction):
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
@app.route('/buildings', methods=['GET', 'POST'])
@app.route('/buildings/<int:building_id>', methods=['GET'])
@login_required
def manage_buildings(building_id=None):
    """
    Gestión de edificios para predicciones
    """
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
        if form.id.data:  # Edición
            building = Building.query.get_or_404(form.id.data)
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
    """
    Eliminar un edificio
    """
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
        model = ensure_model_trained()
        
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
    """API para obtener datos para las gráficas del dashboard"""
    try:
        # Ruta al dataset
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'energy_data.csv')
        
        # Verificar si existe el dataset
        if os.path.exists(data_path):
            data = load_csv_dataset(data_path, validate=False)
        else:
            # Si no existe, usar datos sintéticos
            data = generate_synthetic_data(n_samples=1000)
        
        # Datos de consumo por hora
        consumo_horas = {
            'horas': list(range(24)),
            'consumo': [data[data['hora_dia'] == h]['consumo_energetico'].mean() 
                       for h in range(24)]
        }
        
        # Datos de consumo por día
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        consumo_dias = {
            'dias': dias_semana,
            'consumo': [data[data['dia_semana'] == d]['consumo_energetico'].mean() 
                       for d in range(7)]
        }
        
        # Datos de consumo por edificio (simulado con áreas diferentes)
        areas_edificios = [1000, 2000, 3000, 4000, 5000]
        edificios = ['Edificio A', 'Edificio B', 'Edificio C', 'Edificio D', 'Edificio E']
        
        consumo_edificios = {
            'edificios': edificios,
            'consumo': []
        }
        
        # Para cada edificio, calculamos el consumo promedio
        for area in areas_edificios:
            # Filtramos datos cercanos a esta área
            area_min = area * 0.9
            area_max = area * 1.1
            
            consumo_medio = data[(data['area_edificio'] >= area_min) & 
                                 (data['area_edificio'] <= area_max)]['consumo_energetico'].mean()
            
            consumo_edificios['consumo'].append(round(consumo_medio, 2))
        
        return jsonify({
            'consumo_horas': consumo_horas,
            'consumo_dias': consumo_dias,
            'consumo_edificios': consumo_edificios
        })
    
    except Exception as e:
        logger.error(f"Error al generar datos para dashboard: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
# Ruta para gestión de datasets
@app.route('/dataset', methods=['GET', 'POST'])
@login_required
def dataset_management():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Verificar si la solicitud incluye un archivo
        if 'file' not in request.files:
            flash('No se ha seleccionado ningún archivo')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Si el usuario no selecciona un archivo, el navegador 
        # envía un archivo vacío sin nombre
        if file.filename == '':
            flash('No se ha seleccionado ningún archivo')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Validar el archivo CSV antes de guardarlo
                data = load_csv_dataset(file)
                
                # Guardar el archivo en el directorio configurado
                filename = secure_filename('energy_data.csv')
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Asegurar que el directorio existe
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                
                # Guardar el archivo
                data.to_csv(filepath, index=False)
                
                # Obtener estadísticas del dataset
                stats = get_dataset_statistics(data)
                
                flash(f'Archivo cargado con éxito: {len(data)} registros')
                
                # Reentrena el modelo con los nuevos datos si se solicita
                if 'retrain' in request.form and request.form['retrain'] == 'yes':
                    try:
                        # Preprocesar datos
                        X, y = preprocess_data(data, training=True)
                        
                        # Entrenar modelo
                        model = Energy_Model()
                        metrics = model.train(X, y)
                        
                        flash(f'Modelo reentrenado con éxito. R² = {metrics["r2"]:.4f}')
                    except Exception as e:
                        flash(f'Error al reentrenar el modelo: {str(e)}')
                
                return render_template(
                    'dataset.html', 
                    stats=stats, 
                    filename=filename,
                    success=True
                )
            
            except Exception as e:
                flash(f'Error al procesar el archivo: {str(e)}')
                return redirect(request.url)
        else:
            flash('Tipo de archivo no permitido. Por favor, sube un archivo CSV.')
            return redirect(request.url)
    
    # Para solicitudes GET, mostrar página de gestión de datasets
    try:
        # Verificar si existe un dataset actual
        dataset_path = os.path.join(app.config['UPLOAD_FOLDER'], 'energy_data.csv')
        if os.path.exists(dataset_path):
            data = load_csv_dataset(dataset_path, validate=False)
            stats = get_dataset_statistics(data)
            return render_template('dataset.html', stats=stats, filename='energy_data.csv')
        else:
            return render_template('dataset.html')
    except Exception as e:
        flash(f'Error al cargar información del dataset: {str(e)}')
        return render_template('dataset.html', error=str(e))

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

@app.route('/retrain', methods=['POST'])
@login_required
def retrain_model():
    if current_user.role != 'admin':
        flash('No tienes permisos para realizar esta acción.')
        return redirect(url_for('index'))
    
    try:
        # Cargar dataset
        data_path = os.path.join(app.config['UPLOAD_FOLDER'], 'energy_data.csv')
        
        if not os.path.exists(data_path):
            flash('No se encontró un dataset para entrenar el modelo. Cargue un dataset primero.')
            return redirect(url_for('dataset_management'))
        
        # Cargar los datos
        data = load_csv_dataset(data_path)
        
        # Preprocesar datos
        X, y = preprocess_data(data, training=True)
        
        # Inicializar y entrenar el modelo
        model = Energy_Model()
        metrics = model.train(X, y)
        
        flash(f'Modelo reentrenado con éxito. Métricas: R² = {metrics["r2"]:.4f}, RMSE = {metrics["rmse"]:.4f}')
        return redirect(url_for('admin_panel'))
    
    except Exception as e:
        logger.error(f"Error al reentrenar el modelo: {str(e)}")
        flash(f'Error al reentrenar el modelo: {str(e)}')
        return redirect(url_for('admin_panel'))
    
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
        
        # Obtener predicciones del mes actual
        current_month_predictions = Prediction.query.filter(
            extract('month', Prediction.timestamp) == current_month,
            extract('year', Prediction.timestamp) == current_year
        ).all()
        
        # Calcular consumo total
        if current_month_predictions:
            total_consumption = sum(p.consumo_predicho for p in current_month_predictions) / 30
            total_consumption = round(total_consumption, 2)
        else:
            total_consumption = 0
        
        # Calcular cambio porcentual respecto al mes anterior
        last_month = current_month - 1 if current_month > 1 else 12
        last_month_year = current_year if current_month > 1 else current_year - 1
        
        last_month_predictions = Prediction.query.filter(
            extract('month', Prediction.timestamp) == last_month,
            extract('year', Prediction.timestamp) == last_month_year
        ).all()
        
        if last_month_predictions:
            last_month_consumption = sum(p.consumo_predicho for p in last_month_predictions) / 30
            if last_month_consumption > 0:
                consumption_change = round((total_consumption - last_month_consumption) / last_month_consumption * 100, 1)
            else:
                consumption_change = 0
        else:
            consumption_change = 0
        
        # Detalles de cada edificio
        buildings_details = []
        for building in buildings:
            # Obtener predicciones para este edificio
            building_predictions = Prediction.query.filter_by(building_id=building.id).all()
            prediction_count = len(building_predictions)
            
            # Calcular promedios (si hay predicciones)
            if building_predictions:
                avg_consumption = sum(p.consumo_predicho for p in building_predictions) / prediction_count
                avg_occupancy = sum(p.ocupacion for p in building_predictions) / prediction_count
            else:
                avg_consumption = 0
                avg_occupancy = 0
            
            buildings_details.append({
                'id': building.id,
                'name': building.name,
                'area': building.area,
                'avg_consumption': round(avg_consumption, 2),
                'avg_occupancy': round(avg_occupancy, 1),
                'prediction_count': prediction_count
            })
        
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

if __name__ == '__main__':
    app.run(debug=True)