import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import os
import joblib
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Funciones de utilidad para manejo de archivos
def save_scaler(scaler, scaler_path, model_dir=None):
    """
    Guarda un escalador en disco
    
    Args:
        scaler: Escalador a guardar
        scaler_path (str): Ruta donde guardar el escalador
        model_dir (str, optional): Directorio donde guardar el escalador
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Crear directorio si se especifica y no existe
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
            
        joblib.dump(scaler, scaler_path)
        logger.info(f"Escalador guardado en {scaler_path}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el escalador: {str(e)}")
        return False

def load_scaler(scaler_path):
    """
    Carga un escalador desde disco
    
    Args:
        scaler_path (str): Ruta del escalador
        
    Returns:
        object: Escalador cargado o None si ocurre un error
    """
    try:
        if not os.path.exists(scaler_path):
            logger.warning(f"Escalador no encontrado en '{scaler_path}'")
            return None
            
        scaler = joblib.load(scaler_path)
        logger.info(f"Escalador cargado desde {scaler_path}")
        return scaler
    except Exception as e:
        logger.error(f"Error al cargar el escalador: {str(e)}")
        return None

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
    try:
        # Copia de datos para no modificar el original
        df = data.copy()
        
        # Extraer variable objetivo si existe
        y = None
        if 'consumo_energetico' in df.columns:
            y = df['consumo_energetico']
            df = df.drop('consumo_energetico', axis=1)
        
        # Verificar columnas requeridas
        required_columns = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Columnas requeridas no encontradas: {', '.join(missing_columns)}")
        
        # Aplicar feature engineering
        df = apply_feature_engineering(df)
        
        # Aplicar normalización
        X_processed = normalize_features(df, training)
        
        return X_processed, y
        
    except Exception as e:
        logger.error(f"Error en preprocesamiento de datos: {str(e)}")
        raise

def apply_feature_engineering(df):
    """
    Aplica transformaciones de feature engineering a los datos.
    
    Args:
        df (DataFrame): Datos a transformar
        
    Returns:
        DataFrame: Datos transformados
    """
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
    
    return df

def normalize_features(df, training=True):
    """
    Normaliza las características utilizando StandardScaler.
    
    Args:
        df (DataFrame): Datos a normalizar
        training (bool): Indica si estamos en fase de entrenamiento
        
    Returns:
        DataFrame: Datos normalizados
    """
    # Usar ruta absoluta para el escalador
    model_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    scaler_path = os.path.join(model_dir, 'scaler.pkl')
    
    if training:
        # En entrenamiento, ajustar el escalador y guardarlo
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        
        # Guardar el escalador para uso futuro
        save_scaler(scaler, scaler_path, model_dir)
    else:
        # En predicción, cargar el escalador guardado
        scaler = load_scaler(scaler_path)
        if scaler is None:
            # Si no existe, crear un escalador básico
            logger.warning(f"Escalador no encontrado en '{scaler_path}'. Usando un nuevo escalador.")
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(df)
        else:
            X_scaled = scaler.transform(df)
    
    # Convertir a DataFrame para mantener nombres de columnas
    X_processed = pd.DataFrame(X_scaled, columns=df.columns)
    
    return X_processed