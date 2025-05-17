import os
import pandas as pd
import numpy as np
import logging
from flask import Flask, render_template, request, jsonify, current_app, abort
from energia_app.models.model import Energy_Model
from energia_app.models.preprocess import preprocess_data
from energia_app.utils.data_generator import generate_synthetic_data

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Variable global para el modelo
energy_model = None

def init_model():
    """
    Inicializa y entrena el modelo de predicción energética.
    Crea datos sintéticos si no existen datos de entrenamiento.
    """
    global energy_model
    
    try:
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
        logger.info("Cargando datos y entrenando modelo...")
        train_data = pd.read_csv(data_file)
        X, y = preprocess_data(train_data)
        
        # Inicializar y entrenar modelo
        energy_model = Energy_Model()
        
        # Si el modelo no está entrenado (no se pudo cargar), entrenarlo
        if not energy_model.trained:
            metrics = energy_model.train(X, y)
            logger.info(f"Modelo entrenado exitosamente. Métricas: {metrics}")
        else:
            logger.info("Modelo cargado desde archivo existente.")
        
        return True
    except Exception as e:
        logger.error(f"Error al inicializar el modelo: {str(e)}")
        return False

# Ruta para inicializar el modelo manualmente
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
            
            # Verificar que la ocupación sea coherente con el área
            max_ocupacion_recomendada = area / 5  # 1 persona cada 5 m²
            if ocupacion > max_ocupacion_recomendada:
                logger.warning(f"Ocupación alta para el área: {ocupacion} personas en {area} m²")
            
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
    """
    Genera recomendaciones personalizadas para optimizar el consumo energético.
    
    Args:
        area (float): Área del edificio en m²
        ocupacion (int): Nivel de ocupación en personas
        dia_semana (int): Día de la semana (0-6)
        hora_dia (int): Hora del día (0-23)
        prediction (float): Consumo energético predicho en kWh
    
    Returns:
        list: Lista de recomendaciones personalizadas
    """
    recommendations = []
    
    # Recomendaciones basadas en hora del día
    if 8 <= hora_dia <= 18:  # Horario laboral
        recommendations.append("Optimizar la temperatura de los sistemas de climatización durante las horas pico.")
        
        if 12 <= hora_dia <= 14:  # Hora de almuerzo
            recommendations.append("Considerar apagar luces y equipos no esenciales durante la hora de almuerzo.")
    else:  # Fuera de horario laboral
        recommendations.append("Programar apagado automático de equipos y luces en áreas desocupadas.")
        
        if 0 <= hora_dia <= 6 or 22 <= hora_dia <= 23:  # Noche
            recommendations.append("Implementar un sistema de iluminación exterior con sensores de movimiento y temporizadores.")
    
    # Recomendaciones basadas en ocupación y área
    ocupacion_por_area = ocupacion / area if area > 0 else 0
    
    if ocupacion > 50:
        recommendations.append("Implementar sensores de presencia para optimizar iluminación en áreas de alta ocupación.")
    
    if ocupacion_por_area > 0.1:  # Alta densidad (1 persona cada 10m² o menos)
        recommendations.append("Mejorar los sistemas de ventilación para mantener la calidad del aire sin comprometer la eficiencia energética.")
    
    # Recomendaciones basadas en día de la semana
    if dia_semana >= 5:  # Fin de semana
        recommendations.append("Reducir sistemas de ventilación y climatización en áreas no utilizadas durante fines de semana.")
    else:  # Días laborables
        if ocupacion < area / 30:  # Baja ocupación para un día laboral
            recommendations.append("Ajustar la programación de los sistemas de climatización según la ocupación real del edificio.")
    
    # Recomendaciones basadas en la predicción
    if prediction > 50:  # Consumo alto
        recommendations.append("Considerar la implementación de paneles solares para reducir la dependencia energética en períodos de alto consumo.")
    
    if prediction > area / 20:  # Consumo alto para el área
        recommendations.append("Realizar una auditoría energética para identificar equipos de alto consumo que podrían ser reemplazados por alternativas más eficientes.")
    
    # Limitar a máximo 5 recomendaciones para no abrumar al usuario
    if len(recommendations) > 5:
        recommendations = recommendations[:5]
    
    return recommendations

def generate_dashboard_data():
    """
    Genera datos para el dashboard de visualización.
    
    Returns:
        dict: Datos para las visualizaciones del dashboard
    """
    # Utilizar semilla para consistencia en datos simulados
    np.random.seed(42)
    
    # Generar datos de consumo por hora con patrón realista
    horas = list(range(24))
    # Patrón con valores más altos durante horas laborales
    consumo_base = [10, 9, 8, 7, 6, 7, 12, 25, 40, 48, 45, 
                    50, 52, 55, 53, 50, 45, 42, 35, 30, 25, 20, 15, 12]
    # Añadir variación aleatoria (±10%)
    consumo_horas = [max(1, c + np.random.uniform(-0.1*c, 0.1*c)) for c in consumo_base]
    
    # Generar datos de consumo por día de la semana (menor en fin de semana)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    consumo_dias_base = [50, 48, 52, 49, 45, 20, 15]
    # Añadir variación aleatoria (±5%)
    consumo_dias = [max(1, c + np.random.uniform(-0.05*c, 0.05*c)) for c in consumo_dias_base]
    
    # Generar datos de consumo por edificio
    edificios = ['Bloque A', 'Bloque B', 'Biblioteca', 'Administrativo', 'Laboratorios']
    areas = [2500, 2000, 1500, 1200, 1800]  # áreas aproximadas en m²
    # Consumo proporcional al área con variación
    consumo_edificios = [a * 0.02 * (1 + np.random.uniform(-0.2, 0.2)) for a in areas]
    
    return {
        'consumo_horas': {'horas': horas, 'consumo': consumo_horas},
        'consumo_dias': {'dias': dias, 'consumo': consumo_dias},
        'consumo_edificios': {'edificios': edificios, 'consumo': consumo_edificios}
    }

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error='Página no encontrada'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', error='Error interno del servidor'), 500

# Punto de entrada de la aplicación
if __name__ == '__main__':
    # Inicializar el modelo al arrancar
    with app.app_context():
        init_model()
    
    # Determinar puerto desde variable de entorno (útil para despliegues)
    port = int(os.environ.get("PORT", 5000))
    
    # Ejecutar la aplicación
    app.run(host='0.0.0.0', port=port, debug=False)