import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def generate_synthetic_data(n_samples=1000, start_date=None, seed=42):
    """
    Genera datos sintéticos para el modelo de predicción de consumo energético.
    
    Args:
        n_samples (int): Número de muestras a generar
        start_date (datetime, optional): Fecha de inicio para la generación
        seed (int): Semilla para reproducibilidad
    
    Returns:
        DataFrame: Datos sintéticos generados
    """
    # Establecer semilla para reproducibilidad
    np.random.seed(seed)
    random.seed(seed)
    
    # Fecha de inicio por defecto (si no se proporciona)
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    
    # Generar fechas aleatorias dentro de un año desde la fecha de inicio
    dates = [start_date + timedelta(days=random.randint(0, 365), hours=random.randint(0, 23)) 
             for _ in range(n_samples)]
    
    # Extraer características temporales
    dia_semana = [date.weekday() for date in dates]  # 0: Lunes, 6: Domingo
    hora_dia = [date.hour for date in dates]
    
    # Generar áreas de edificios (m²) entre 500 y 5000 m²
    areas = np.random.uniform(500, 5000, n_samples)
    
    # Generar niveles de ocupación (personas)
    # Asumimos una relación entre área y capacidad máxima (~1 persona cada 10 m²)
    ocupacion_max = areas / 10
    
    # La ocupación real varía según hora y día
    ocupacion = []
    for i in range(n_samples):
        # Ocupación base 
        base_ocupacion = ocupacion_max[i] * 0.8  # 80% de capacidad máxima como base
        
        # Factor de día (menor en fines de semana)
        day_factor = 0.3 if dia_semana[i] >= 5 else 1.0
        
        # Factor de hora (mayor durante horas laborales 8-18)
        hour_factor = 0.9 if 8 <= hora_dia[i] <= 18 else 0.2
        
        # Ocupación final con algo de aleatoriedad
        ocup = int(base_ocupacion * day_factor * hour_factor * random.uniform(0.7, 1.1))
        ocupacion.append(ocup)
    
    # Generar consumo energético basado en los factores anteriores
    # Fórmula base: consumo = α*área + β*ocupación + factores temporales + ruido
    
    # Coeficientes base
    alpha = 0.05  # Factor de área
    beta = 0.3    # Factor de ocupación
    
    consumo = []
    for i in range(n_samples):
        # Base: relacionada con área y ocupación
        base_consumo = alpha * areas[i] + beta * ocupacion[i]
        
        # Factor día de semana (menor en fines de semana)
        day_factor = 0.6 if dia_semana[i] >= 5 else 1.0
        
        # Factor hora (patrón con pico en horas laborales)
        if 8 <= hora_dia[i] <= 18:
            # Durante horas laborales, pico a media mañana y media tarde
            hour_peak = 1.0
            if 10 <= hora_dia[i] <= 12 or 15 <= hora_dia[i] <= 17:
                hour_peak = 1.2
            hour_factor = hour_peak
        else:
            # Fuera de horas laborales, consumo base
            hour_factor = 0.4
        
        # Ruido aleatorio (±10%)
        noise = random.uniform(0.9, 1.1)
        
        # Consumo final
        c = base_consumo * day_factor * hour_factor * noise
        consumo.append(c)
    
    # Crear DataFrame
    data = pd.DataFrame({
        'area_edificio': areas,
        'ocupacion': ocupacion,
        'dia_semana': dia_semana,
        'hora_dia': hora_dia,
        'consumo_energetico': consumo
    })
    
    return data

def generate_future_scenarios(edificio_area, dias=7, model=None):
    """
    Genera escenarios futuros para predicción.
    
    Args:
        edificio_area (float): Área del edificio en m²
        dias (int): Número de días a predecir
        model: Modelo entrenado
    
    Returns:
        DataFrame: Escenarios generados con predicciones si se proporciona modelo
    """
    # Fecha actual
    now = datetime.now()
    
    # Generar escenarios para cada hora del día para los próximos días
    scenarios = []
    
    for day in range(dias):
        # Fecha actual + N días
        date = now + timedelta(days=day)
        dia_semana = date.weekday()
        
        for hora in range(24):
            # Calcular ocupación estimada basada en patrones conocidos
            ocupacion_base = edificio_area / 10  # Capacidad máxima estimada
            
            # Ajustar por día de semana y hora
            day_factor = 0.3 if dia_semana >= 5 else 1.0
            hour_factor = 0.9 if 8 <= hora <= 18 else 0.2
            
            ocupacion = int(ocupacion_base * day_factor * hour_factor)
            
            scenario = {
                'fecha': date.strftime('%Y-%m-%d'),
                'dia_semana': dia_semana,
                'hora_dia': hora,
                'area_edificio': edificio_area,
                'ocupacion': ocupacion
            }
            
            scenarios.append(scenario)
    
    # Crear DataFrame
    df_scenarios = pd.DataFrame(scenarios)
    
    # Si se proporciona modelo, realizar predicciones
    if model is not None:
        try:
            # Importar correctamente el módulo de preprocesamiento
            # Solución más robusta:
            import importlib
            import sys
            
            # Asegurar que el módulo principal está en el sys.path
            module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            if module_path not in sys.path:
                sys.path.insert(0, module_path)
                
            # Importar dinámicamente
            preprocess = importlib.import_module('models.preprocess')
            
            # Preprocesar datos
            X, _ = preprocess.preprocess_data(df_scenarios, training=False)
            
            # Realizar predicciones
            predictions = model.predict(X)
            
            # Añadir predicciones al DataFrame
            df_scenarios['consumo_predicho'] = predictions
        except ImportError as e:
            # Manejo específico del error
            logger.warning(f"No se pudo importar el módulo de preprocesamiento: {str(e)}")
            logger.warning("No se realizarán predicciones en los escenarios futuros.")
        except Exception as e:
            # Otros errores
            logger.error(f"Error al generar predicciones: {str(e)}")
    
    return df_scenarios