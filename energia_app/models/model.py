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
        if os.path.exists(self.model_path):
            try:
                self.load_model()
                logger.info(f"Modelo cargado desde {self.model_path}")
            except Exception as e:
                logger.error(f"Error al cargar el modelo: {str(e)}")
    
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
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            # Guardar modelo entrenado
            self.save_model()
            
            metrics = {
                'mse': mse,
                'rmse': rmse,
                'r2': r2,
                'coefficients': self.model.coef_.tolist(),  # Convertir a lista para mejor serialización
                'intercept': float(self.model.intercept_)   # Convertir a float nativo
            }
            
            logger.info(f"Modelo entrenado. Métricas: MSE={mse:.4f}, R²={r2:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error al entrenar el modelo: {str(e)}")
            raise
    
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
        try:
            # Crear directorio si no existe
            os.makedirs(self.model_dir, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            logger.info(f"Modelo guardado en {self.model_path}")
        except Exception as e:
            logger.error(f"Error al guardar el modelo: {str(e)}")
            raise
    
    def load_model(self):
        """Carga el modelo entrenado desde disco"""
        try:
            self.model = joblib.load(self.model_path)
            self.trained = True
        except Exception as e:
            logger.error(f"Error al cargar el modelo: {str(e)}")
            raise
    
    def get_feature_importance(self):
        """
        Obtiene la importancia relativa de cada característica
        
        Returns:
            dict: Importancia de cada característica
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