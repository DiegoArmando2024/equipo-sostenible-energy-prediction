import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def preprocess_data(data_df, training=False):
    """Preprocesa datos para el modelo de energía"""
    try:
        # Crear directorio para escaladores si no existe
        os.makedirs('energia_app/models/scalers', exist_ok=True)
        
        # Copiar los datos para no modificar el DataFrame original
        processed_df = data_df.copy()
        
        # Codificación de variables categóricas
        if 'dia_semana' in processed_df.columns:
            processed_df['dia_semana'] = processed_df['dia_semana'].astype(int) % 7
            
        if 'hora_dia' in processed_df.columns:
            processed_df['hora_dia'] = processed_df['hora_dia'].astype(int) % 24
        
        # Escalado de características
        if training:
            scaler = StandardScaler()
            scaled_features = scaler.fit_transform(processed_df[['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia']])
            
            # Guardar el escalador
            scaler_path = 'energia_app/models/scalers/energy_scaler.pkl'
            joblib.dump(scaler, scaler_path)
            logger.info(f"Escalador guardado en {scaler_path}")
        else:
            # Cargar escalador existente
            scaler_path = 'energia_app/models/scalers/energy_scaler.pkl'
            if not os.path.exists(scaler_path):
                raise FileNotFoundError(f"Escalador no encontrado en {scaler_path}")
                
            scaler = joblib.load(scaler_path)
            scaled_features = scaler.transform(processed_df[['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia']])
        
        # Separar características y objetivo
        X = scaled_features
        y = processed_df['consumo_energetico'].values if 'consumo_energetico' in processed_df.columns else None
        
        return X, y
        
    except Exception as e:
        logger.error(f"Error en preprocesamiento: {str(e)}")
        raise