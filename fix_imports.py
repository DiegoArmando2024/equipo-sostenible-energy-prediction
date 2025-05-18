
"""
Utilidades para cargar y procesar datos de consumo energético.
Este archivo proporciona compatibilidad con la versión anterior del código
mientras se migra al enfoque centrado en la base de datos.
"""

import os
import pandas as pd
import logging

# Configurar logging
logger = logging.getLogger(__name__)

def load_csv_dataset(file_path, validate=True):
    """
    Carga un dataset desde un archivo CSV.
    
    Args:
        file_path (str): Ruta al archivo CSV
        validate (bool): Si se debe validar el formato
        
    Returns:
        DataFrame: Datos cargados
    """
    try:
        # Verificar si existe el archivo
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
        
        # Cargar datos
        data = pd.read_csv(file_path)
        
        # Validar columnas requeridas
        if validate:
            required_cols = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                raise ValueError(f"El dataset no tiene las columnas requeridas: {', '.join(missing_cols)}")
        
        return data
    except Exception as e:
        logger.error(f"Error al cargar dataset desde {file_path}: {str(e)}")
        raise

def save_dataset(data, file_path):
    """
    Guarda un dataset en un archivo CSV.
    
    Args:
        data (DataFrame): DataFrame a guardar
        file_path (str): Ruta donde guardar el archivo
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Guardar como CSV
        data.to_csv(file_path, index=False)
        logger.info(f"Dataset guardado en {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar dataset en {file_path}: {str(e)}")
        return False

def get_dataset_statistics(data):
    """
    Calcula estadísticas del dataset.
    
    Args:
        data (DataFrame): DataFrame con los datos
        
    Returns:
        dict: Estadísticas del dataset
    """
    try:
        # Calcular estadísticas básicas
        stats = {
            'n_samples': len(data),
            'area_min': data['area_edificio'].min(),
            'area_max': data['area_edificio'].max(),
            'consumo_min': data['consumo_energetico'].min(),
            'consumo_max': data['consumo_energetico'].max(),
            'consumo_mean': data['consumo_energetico'].mean()
        }
        
        # Calcular correlaciones
        correlaciones = {
            'area_consumo': data['area_edificio'].corr(data['consumo_energetico']),
            'ocupacion_consumo': data['ocupacion'].corr(data['consumo_energetico']),
            'dia_consumo': data['dia_semana'].corr(data['consumo_energetico']),
            'hora_consumo': data['hora_dia'].corr(data['consumo_energetico'])
        }
        
        stats['correlaciones'] = correlaciones
        
        return stats
    except Exception as e:
        logger.error(f"Error al calcular estadísticas: {str(e)}")
        return {
            'n_samples': len(data),
            'error': str(e)
        }
