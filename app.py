import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
from models.model import Energy_Model
from models.preprocess import preprocess_data
from utils.data_generator import generate_synthetic_data

app = Flask(__name__)

# Inicializar y entrenar el modelo al inicio de la aplicación
@app.before_first_request
def initialize_model():
    global energy_model
    
    # Generar datos sintéticos para entrenamiento (si no existen)
    if not os.path.exists('data'):
        os.makedirs('data')
    
    if not os.path.exists('data/synthetic_energy_data.csv'):
        print("Generando datos sintéticos para entrenamiento...")
        data = generate_synthetic_data(n_samples=1000)
        data.to_csv('data/synthetic_energy_data.csv', index=False)
    
    # Cargar datos y entrenar modelo
    print("Cargando datos y entrenando modelo...")
    train_data = pd.read_csv('data/synthetic_energy_data.csv')
    X, y = preprocess_data(train_data)
    
    # Inicializar y entrenar modelo
    energy_model = Energy_Model()
    energy_model.train(X, y)
    print("Modelo entrenado exitosamente.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        # Obtener datos del formulario
        area = float(request.form['area'])
        ocupacion = int(request.form['ocupacion'])
        dia_semana = int(request.form['dia_semana'])
        hora_dia = int(request.form['hora_dia'])
        
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
    
    return render_template('prediction.html')

@app.route('/dashboard')
def dashboard():
    # Generar datos para el dashboard
    data = generate_dashboard_data()
    return render_template('dashboard.html', data=data)

@app.route('/api/data')
def get_data():
    # Endpoint API para obtener datos para visualizaciones
    data = generate_dashboard_data()
    return jsonify(data)

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

if __name__ == '__main__':
    app.run(debug=True)