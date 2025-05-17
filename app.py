from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
import pandas as pd
import numpy as np
import logging
from energia_app.models import Energy_Model, preprocess_data
from energia_app.utils import generate_synthetic_data, generate_future_scenarios
from energia_app.models.user import db, User
from energia_app.forms import LoginForm, RegistrationForm

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


# Asegurar que el modelo está entrenado
def ensure_model_trained():
    model = Energy_Model()
    
    # Si el modelo no está entrenado, generamos datos sintéticos y lo entrenamos
    if not model.trained:
        logger.info("Modelo no entrenado. Generando datos sintéticos para entrenar...")
        data = generate_synthetic_data(n_samples=1000)
        
        # Guardar los datos para referencia futura
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'energia_app', 'data')
        os.makedirs(data_dir, exist_ok=True)
        data.to_csv(os.path.join(data_dir, 'synthetic_energy_data.csv'), index=False)
        
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
        admin = User(username='admin', email='admin@example.com', role='admin')
        admin.set_password('adminpassword')
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
        return redirect(url_for('index'))
    
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
def index():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        # Obtener parámetros del formulario
        area = float(request.form['area'])
        ocupacion = int(request.form['ocupacion'])
        dia_semana = int(request.form['dia_semana'])
        hora_dia = int(request.form['hora_dia'])
        
        # Crear DataFrame con los datos de entrada
        input_data = pd.DataFrame({
            'area_edificio': [area],
            'ocupacion': [ocupacion],
            'dia_semana': [dia_semana],
            'hora_dia': [hora_dia]
        })
        
        try:
            # Asegurar que el modelo está entrenado
            model = ensure_model_trained()
            
            # Preprocesar datos de entrada
            X, _ = preprocess_data(input_data, training=False)
            
            # Realizar predicción
            prediction = model.predict(X)[0]
            
            # Redondear predicción a 2 decimales
            prediction = round(float(prediction), 2)
            
            # Generar recomendaciones
            recommendations = generate_recommendations(area, ocupacion, dia_semana, hora_dia, prediction)
            
            # Renderizar template con resultado
            return render_template('prediction.html', 
                                  prediction=prediction,
                                  area=area,
                                  ocupacion=ocupacion,
                                  dia_semana=dia_semana,
                                  hora_dia=hora_dia,
                                  recommendations=recommendations)
        
        except Exception as e:
            logger.error(f"Error al realizar predicción: {str(e)}")
            return render_template('prediction.html', error=str(e))
    
    # Si es GET, mostrar formulario
    return render_template('prediction.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/data')
def get_data():
    """API para obtener datos para las gráficas del dashboard"""
    try:
        # Asegurar que el modelo está entrenado
        model = ensure_model_trained()
        
        # Cargar datos (si existen, sino generar nuevos)
        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                'energia_app', 'data', 'synthetic_energy_data.csv')
        
        if os.path.exists(data_path):
            data = pd.read_csv(data_path)
        else:
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
    
# Rutas de administración
@app.route('/admin')
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.')
        return redirect(url_for('index'))
    
    users = User.query.all()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)