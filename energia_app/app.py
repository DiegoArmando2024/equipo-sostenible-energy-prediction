import os
import pandas as pd
import numpy as np
import random  # Importación añadida
import logging
from flask import Flask, render_template, request, jsonify, current_app
from models.model import Energy_Model
from models.preprocess import preprocess_data
from utils.data_generator import generate_synthetic_data

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variable global para el modelo
energy_model = None

# Función para inicializar el modelo (ya no usa el decorador obsoleto)
def init_model():
    global energy_model
    
    logger.info("Iniciando la inicialización del modelo...")
    
    # Asegurar que existe el directorio data
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    data_file = os.path.join(data_dir, 'synthetic_energy_data.csv')
    
    # Generar datos sintéticos para entrenamiento (si no existen)
    if not os.path.exists(data_file):
        logger.info("Generando datos sintéticos para entrenamiento...")
        data = generate_synthetic_data(n_samples=1000)
        data.to_csv(data_file, index=False)
    
    # Cargar datos y entrenar modelo
    try:
        logger.info("Cargando datos y entrenando modelo...")
        train_data = pd.read_csv(data_file)
        X, y = preprocess_data(train_data)
        
        # Inicializar y entrenar modelo
        energy_model = Energy_Model()
        metrics = energy_model.train(X, y)
        logger.info(f"Modelo entrenado exitosamente. Métricas: {metrics}")
        return True
    except Exception as e:
        logger.error(f"Error al inicializar el modelo: {str(e)}")
        return False

# Ruta para inicializar el modelo manualmente si es necesario
@app.route('/initialize')
def initialize_model():
    success = init_model()
    if success:
        return "Modelo inicializado correctamente."
    return "Error al inicializar el modelo. Consulte los logs.", 500

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    global energy_model
    
    # Verificar que el modelo esté inicializado
    if energy_model is None or not energy_model.trained:
        logger.warning("Modelo no inicializado. Inicializando ahora...")
        init_model()
        if energy_model is None or not energy_model.trained:
            return "Error: El modelo no pudo ser inicializado. Por favor, inténtelo de nuevo más tarde.", 500
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario con validación
            area = float(request.form.get('area', 1000))
            if area < 100 or area > 10000:
                return "Error: El área debe estar entre 100 y 10000 m²", 400
                
            ocupacion = int(request.form.get('ocupacion', 50))
            if ocupacion < 0 or ocupacion > 1000:
                return "Error: La ocupación debe estar entre 0 y 1000 personas", 400
                
            dia_semana = int(request.form.get('dia_semana', 0))
            if dia_semana < 0 or dia_semana > 6:
                return "Error: Día de semana inválido", 400
                
            hora_dia = int(request.form.get('hora_dia', 12))
            if hora_dia < 0 or hora_dia > 23:
                return "Error: Hora del día inválida", 400
            
            # Crear dataframe con los datos de entrada
            input_data = pd.DataFrame({
                'area_edificio': [area],
                'ocupacion': [ocupacion],
                'dia_semana': [dia_semana],
                'hora_dia': [hora_dia]
            })
            
            # Preprocesar datos de entrada
            X_input, _ = preprocess_data(input_data, training=False)
            
            # Realizar predicción
            prediction = energy_model.predict(X_input)
            
            # Obtener recomendaciones basadas en la predicción
            recommendations = get_recommendations(area, ocupacion, dia_semana, hora_dia, prediction[0])
            
            return render_template('prediction.html', 
                                  prediction=round(prediction[0], 2),
                                  area=area,
                                  ocupacion=ocupacion, 
                                  dia_semana=dia_semana,
                                  hora_dia=hora_dia,
                                  recommendations=recommendations)
        except Exception as e:
            logger.error(f"Error en la predicción: {str(e)}")
            return f"Error en la predicción: {str(e)}", 500
    
    return render_template('prediction.html')

@app.route('/dashboard')
def dashboard():
    # Generar datos para el dashboard
    try:
        data = generate_dashboard_data()
        return render_template('dashboard.html', data=data)
    except Exception as e:
        logger.error(f"Error al generar dashboard: {str(e)}")
        return f"Error al generar datos para el dashboard: {str(e)}", 500

@app.route('/api/data')
def get_data():
    # Endpoint API para obtener datos para visualizaciones
    try:
        data = generate_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error en API /api/data: {str(e)}")
        return jsonify({"error": str(e)}), 500

def get_recommendations(area, ocupacion, dia_semana, hora_dia, prediction):
    """Genera recomendaciones para optimizar el consumo energético"""
    recommendations = []
    
    # Recomendaciones basadas en hora del día
    if 8 <= hora_dia <= 18:  # Horario laboral
        recommendations.append("Optimizar la temperatura de los sistemas de climatización durante las horas pico.")
    else:  # Fuera de horario laboral
        recommendations.append("Programar apagado automático de equipos y luces en áreas desocupadas.")
    
    # Recomendaciones basadas en ocupación
    if ocupacion > 50:
        recommendations.append("Implementar sensores de presencia para optimizar iluminación en áreas de alta ocupación.")
    
    # Recomendaciones basadas en día de la semana
    if dia_semana >= 5:  # Fin de semana
        recommendations.append("Reducir sistemas de ventilación y climatización en áreas no utilizadas durante fines de semana.")
    
    # Recomendaciones basadas en la predicción
    if prediction > 50:  # Consumo alto
        recommendations.append("Considerar la implementación de paneles solares para reducir la dependencia energética en períodos de alto consumo.")
    
    return recommendations

def generate_dashboard_data():
    """Genera datos para el dashboard de visualización"""
    # Generar datos de consumo por hora
    horas = list(range(24))
    consumo_horas = [10 + 5*h + random.randint(-5, 5) if 8 <= h <= 18 else 5 + random.randint(-2, 2) for h in horas]
    
    # Generar datos de consumo por día de la semana
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    consumo_dias = [50, 48, 52, 49, 45, 20, 15]
    
    # Generar datos de consumo por edificio
    edificios = ['Bloque A', 'Bloque B', 'Biblioteca', 'Administrativo', 'Laboratorios']
    consumo_edificios = [65, 48, 35, 42, 55]
    
    return {
        'consumo_horas': {'horas': horas, 'consumo': consumo_horas},
        'consumo_dias': {'dias': dias, 'consumo': consumo_dias},
        'consumo_edificios': {'edificios': edificios, 'consumo': consumo_edificios}
    }

# Punto de entrada de la aplicación
if __name__ == '__main__':
    with app.app_context():
        init_model()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)