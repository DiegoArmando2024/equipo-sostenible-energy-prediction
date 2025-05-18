import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Funciones de utilidad para manejo de modelos
def save_model_file(model, model_path, model_dir=None):
    """
    Guarda un modelo en disco
    
    Args:
        model: Modelo a guardar
        model_path (str): Ruta donde guardar el modelo
        model_dir (str, optional): Directorio donde guardar el modelo
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Crear directorio si se especifica y no existe
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        elif not os.path.exists(os.path.dirname(model_path)):
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            
        joblib.dump(model, model_path)
        logger.info(f"Modelo guardado en {model_path}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el modelo: {str(e)}")
        return False

def load_model_file(model_path):
    """
    Carga un modelo desde disco
    
    Args:
        model_path (str): Ruta del modelo
        
    Returns:
        object: Modelo cargado o None si ocurre un error
    """
    try:
        if not os.path.exists(model_path):
            logger.warning(f"Modelo no encontrado en '{model_path}'")
            return None
            
        model = joblib.load(model_path)
        logger.info(f"Modelo cargado desde {model_path}")
        return model
    except Exception as e:
        logger.error(f"Error al cargar el modelo: {str(e)}")
        return None

class Energy_Model:
    """
    Modelo de regresión lineal para predecir el consumo energético
    basado en área del edificio, ocupación, día de la semana y hora del día.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
        
        # Usar ruta absoluta para el modelo
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model_dir = os.path.join(base_dir, 'models')
        self.model_path = os.path.join(self.model_dir, 'energy_model.pkl')
        
        # Cargar modelo si existe
        self._try_load_model()
    
    def _try_load_model(self):
        """Intenta cargar el modelo existente"""
        loaded_model = load_model_file(self.model_path)
        if loaded_model:
            self.model = loaded_model
            self.trained = True
    
    def train(self, X, y, test_size=0.2, random_state=42):
        """
        Entrena el modelo con los datos proporcionados
        
        Args:
            X (DataFrame): Características de entrada
            y (Series): Variable objetivo (consumo energético)
            test_size (float): Proporción de datos para prueba
            random_state (int): Semilla para reproducibilidad
        
        Returns:
            dict: Métricas de rendimiento del modelo
        """
        try:
            # Dividir datos en entrenamiento y prueba
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )
            
            # Entrenar modelo
            self.model.fit(X_train, y_train)
            self.trained = True
            
            # Evaluar modelo
            y_pred = self.model.predict(X_test)
            
            # Calcular métricas
            metrics = self._calculate_metrics(y_test, y_pred)
            
            # Guardar modelo entrenado
            self.save_model()
            
            logger.info(f"Modelo entrenado. Métricas: MSE={metrics['mse']:.4f}, R²={metrics['r2']:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error al entrenar el modelo: {str(e)}")
            raise
    
    def _calculate_metrics(self, y_true, y_pred):
        """
        Calcula métricas de rendimiento del modelo
        
        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            
        Returns:
            dict: Métricas de rendimiento
        """
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_true, y_pred)
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'coefficients': self.model.coef_.tolist(),
            'intercept': float(self.model.intercept_)
        }
    
    def predict(self, X):
        """
        Realiza predicciones con el modelo entrenado
        
        Args:
            X (DataFrame): Características de entrada
        
        Returns:
            array: Predicciones de consumo energético
        """
        if not self.trained:
            raise ValueError("El modelo no ha sido entrenado aún.")
        
        try:
            predictions = self.model.predict(X)
            return predictions
        except Exception as e:
            logger.error(f"Error al realizar predicción: {str(e)}")
            raise
    
    def save_model(self):
        """Guarda el modelo entrenado en disco"""
        return save_model_file(self.model, self.model_path, self.model_dir)
    
    def load_model(self):
        """Carga el modelo entrenado desde disco"""
        loaded_model = load_model_file(self.model_path)
        if loaded_model:
            self.model = loaded_model
            self.trained = True
            return True
        return False
    
    def get_feature_importance(self):
        """
        Obtiene la importancia relativa de cada característica
        
        Returns:
            ndarray: Importancia de cada característica
        """
        if not self.trained:
            raise ValueError("El modelo no ha sido entrenado aún.")
        
        try:
            # Obtener coeficientes absolutos
            importance = np.abs(self.model.coef_)
            
            # Normalizar para obtener importancia relativa
            importance = importance / np.sum(importance)
            
            return importance
        except Exception as e:
            logger.error(f"Error al calcular importancia de características: {str(e)}")
            raise