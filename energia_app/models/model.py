import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

class Energy_Model:
    """
    Modelo de regresión lineal para predecir el consumo energético
    basado en área del edificio, ocupación, día de la semana y hora del día.
    """
    
    def __init__(self):
        self.model = LinearRegression()
        self.trained = False
        self.model_path = 'models/energy_model.pkl'
        
        # Cargar modelo si existe
        if os.path.exists(self.model_path):
            self.load_model()
    
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
        
        return {
            'mse': mse,
            'rmse': rmse,
            'r2': r2,
            'coefficients': self.model.coef_,
            'intercept': self.model.intercept_
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
        
        return self.model.predict(X)
    
    def save_model(self):
        """Guarda el modelo entrenado en disco"""
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
    
    def load_model(self):
        """Carga el modelo entrenado desde disco"""
        self.model = joblib.load(self.model_path)
        self.trained = True
    
    def get_feature_importance(self):
        """
        Obtiene la importancia relativa de cada característica
        
        Returns:
            dict: Importancia de cada característica
        """
        if not self.trained:
            raise ValueError("El modelo no ha sido entrenado aún.")
        
        # Obtener coeficientes absolutos
        importance = np.abs(self.model.coef_)
        
        # Normalizar para obtener importancia relativa
        importance = importance / np.sum(importance)
        
        return importance