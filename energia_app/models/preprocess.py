import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os
import joblib

def preprocess_data(data, training=True):
    """
    Preprocesa los datos para el modelo de predicción energética.
    
    Args:
        data (DataFrame): Datos a preprocesar
        training (bool): Indica si estamos en fase de entrenamiento
    
    Returns:
        tuple: (X_processed, y) donde X_processed son las características
               procesadas y y es la variable objetivo (si está disponible)
    """
    # Copia de datos para no modificar el original
    df = data.copy()
    
    # Extraer variable objetivo si existe
    y = None
    if 'consumo_energetico' in df.columns:
        y = df['consumo_energetico']
        df = df.drop('consumo_energetico', axis=1)
    
    # Verificar columnas requeridas
    required_columns = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Columna requerida '{col}' no encontrada en los datos.")
    
    # ---- Feature Engineering ----
    
    # 1. Transformar variables cíclicas (día de la semana, hora del día)
    # Día de la semana (0-6) -> seno y coseno para capturar ciclicidad
    df['dia_semana_sin'] = np.sin(2 * np.pi * df['dia_semana'] / 7)
    df['dia_semana_cos'] = np.cos(2 * np.pi * df['dia_semana'] / 7)
    
    # Hora del día (0-23) -> seno y coseno para capturar ciclicidad
    df['hora_dia_sin'] = np.sin(2 * np.pi * df['hora_dia'] / 24)
    df['hora_dia_cos'] = np.cos(2 * np.pi * df['hora_dia'] / 24)
    
    # 2. Crear características derivadas
    # Indicador de día laboral (0-4: días laborales, 5-6: fin de semana)
    df['es_dia_laboral'] = df['dia_semana'].apply(lambda x: 1 if x < 5 else 0)
    
    # Indicador de hora laboral (8-18 horas: horario laboral)
    df['es_hora_laboral'] = df['hora_dia'].apply(lambda x: 1 if 8 <= x <= 18 else 0)
    
    # Interacción entre ocupación y área
    df['ocupacion_por_area'] = df['ocupacion'] / df['area_edificio']
    
    # 3. Eliminar columnas originales de variables cíclicas
    df = df.drop(['dia_semana', 'hora_dia'], axis=1)
    
    # ---- Normalización ----
    scaler_path = 'models/scaler.pkl'
    
    if training:
        # En entrenamiento, ajustar el escalador y guardarlo
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        
        # Guardar el escalador para uso futuro
        os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
        joblib.dump(scaler, scaler_path)
    else:
        # En predicción, cargar el escalador guardado
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Escalador no encontrado en '{scaler_path}'. Entrene primero el modelo.")
        
        scaler = joblib.load(scaler_path)
        X_scaled = scaler.transform(df)
    
    # Convertir a DataFrame para mantener nombres de columnas
    X_processed = pd.DataFrame(X_scaled, columns=df.columns)
    
    return X_processed, y