import pandas as pd
import numpy as np
import os
import logging
from werkzeug.utils import secure_filename

# Configurar logging
logger = logging.getLogger(__name__)

def load_csv_dataset(file, validate=True, required_columns=None):
    """
    Carga un dataset desde un archivo CSV.
    
    Args:
        file: Objeto de archivo CSV cargado a través de Flask o ruta al archivo
        validate (bool): Si se debe validar la estructura del dataset
        required_columns (list): Lista de columnas requeridas para validación
        
    Returns:
        DataFrame: Datos cargados del CSV
    """
    try:
        # Lectura del CSV (independiente de si es ruta o objeto)
        data = pd.read_csv(file)
        
        # Si no se especifican columnas requeridas, usar el conjunto predeterminado
        if required_columns is None:
            required_columns = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']
        
        # Validar el dataset si es necesario
        if validate:
            validate_dataset_structure(data, required_columns)
            validate_dataset_values(data, required_columns)
        
        return data
    
    except Exception as e:
        logger.error(f"Error al cargar el dataset: {str(e)}")
        raise

def validate_dataset_structure(data, required_columns):
    """
    Valida la estructura del dataset (columnas y valores nulos).
    
    Args:
        data (DataFrame): Dataset a validar
        required_columns (list): Lista de columnas requeridas
    
    Raises:
        ValueError: Si la validación falla
    """
    # Verificar columnas requeridas
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        raise ValueError(f"Columnas requeridas no encontradas: {', '.join(missing_columns)}")
    
    # Verificar que no haya valores nulos en columnas críticas
    null_counts = data[required_columns].isnull().sum()
    if null_counts.sum() > 0:
        columns_with_nulls = [col for col in required_columns if null_counts[col] > 0]
        raise ValueError(f"Se encontraron valores nulos en columnas críticas: {', '.join(columns_with_nulls)}")

def validate_dataset_values(data, required_columns):
    """
    Valida los valores del dataset (tipos y rangos).
    
    Args:
        data (DataFrame): Dataset a validar
        required_columns (list): Lista de columnas requeridas
    
    Raises:
        ValueError: Si la validación falla
    """
    # Validaciones sólo si las columnas están presentes
    if 'area_edificio' in data.columns:
        # area_edificio debe ser numérico
        if not pd.api.types.is_numeric_dtype(data['area_edificio']):
            raise ValueError("La columna 'area_edificio' debe ser numérica")
    
    if 'ocupacion' in data.columns:
        # ocupacion debe ser entero positivo
        if not pd.api.types.is_integer_dtype(data['ocupacion']):
            # Intentar convertir a entero
            try:
                data['ocupacion'] = data['ocupacion'].astype(int)
            except:
                raise ValueError("La columna 'ocupacion' debe contener valores enteros")
    
    if 'dia_semana' in data.columns:
        # dia_semana debe ser 0-6
        if not all(0 <= x <= 6 for x in data['dia_semana'].dropna()):
            raise ValueError("La columna 'dia_semana' debe contener valores entre 0 y 6")
    
    if 'hora_dia' in data.columns:
        # hora_dia debe ser 0-23
        if not all(0 <= x <= 23 for x in data['hora_dia'].dropna()):
            raise ValueError("La columna 'hora_dia' debe contener valores entre 0 y 23")
    
    if 'consumo_energetico' in data.columns:
        # consumo_energetico debe ser numérico positivo
        if not pd.api.types.is_numeric_dtype(data['consumo_energetico']):
            raise ValueError("La columna 'consumo_energetico' debe ser numérica")
        
        if (data['consumo_energetico'] < 0).any():
            raise ValueError("La columna 'consumo_energetico' no debe contener valores negativos")

def save_dataset(data, filename, directory='data'):
    """
    Guarda un dataset en un archivo CSV.
    
    Args:
        data (DataFrame): Dataset a guardar
        filename (str): Nombre del archivo
        directory (str): Directorio donde guardar el archivo
        
    Returns:
        str: Ruta al archivo guardado
    """
    try:
        # Asegurar que el directorio existe
        os.makedirs(directory, exist_ok=True)
        
        # Crear ruta completa
        filepath = os.path.join(directory, secure_filename(filename))
        
        # Guardar dataset
        data.to_csv(filepath, index=False)
        
        logger.info(f"Dataset guardado en {filepath}")
        return filepath
    
    except Exception as e:
        logger.error(f"Error al guardar el dataset: {str(e)}")
        raise

def get_dataset_statistics(data):
    """
    Calcula estadísticas descriptivas del dataset.
    
    Args:
        data (DataFrame): Dataset a analizar
        
    Returns:
        dict: Estadísticas del dataset
    """
    try:
        # Estadísticas básicas
        stats = calculate_basic_stats(data)
        
        # Correlaciones
        stats['correlaciones'] = calculate_correlations(data)
        
        return stats
    
    except Exception as e:
        logger.error(f"Error al calcular estadísticas del dataset: {str(e)}")
        raise

def calculate_basic_stats(data):
    """
    Calcula estadísticas básicas del dataset.
    
    Args:
        data (DataFrame): Dataset a analizar
        
    Returns:
        dict: Estadísticas básicas
    """
    return {
        'n_samples': len(data),
        'area_min': data['area_edificio'].min(),
        'area_max': data['area_edificio'].max(),
        'area_mean': data['area_edificio'].mean(),
        'ocupacion_min': data['ocupacion'].min(),
        'ocupacion_max': data['ocupacion'].max(),
        'ocupacion_mean': data['ocupacion'].mean(),
        'consumo_min': data['consumo_energetico'].min(),
        'consumo_max': data['consumo_energetico'].max(),
        'consumo_mean': data['consumo_energetico'].mean(),
        'consumo_std': data['consumo_energetico'].std(),
        'dias_semana': data['dia_semana'].value_counts().to_dict(),
        'horas_dia': data['hora_dia'].value_counts().to_dict()
    }

def calculate_correlations(data):
    """
    Calcula correlaciones entre variables del dataset.
    
    Args:
        data (DataFrame): Dataset a analizar
        
    Returns:
        dict: Correlaciones
    """
    # Calcular correlaciones
    correlations = data[['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']].corr()
    return {
        'area_consumo': correlations.loc['area_edificio', 'consumo_energetico'],
        'ocupacion_consumo': correlations.loc['ocupacion', 'consumo_energetico'],
        'dia_consumo': correlations.loc['dia_semana', 'consumo_energetico'],
        'hora_consumo': correlations.loc['hora_dia', 'consumo_energetico']
    }
