import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import joblib
def train_model():
    # Cargar datos
    data = pd.read_csv("data/synthetic_data.csv")
    
    # Dividir datos en características y etiqueta
    X = data[['area', 'people', 'day', 'hour']]
    y = data['consumption']
    
    # Dividir datos en conjunto de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Entrenar modelo
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Guardar modelo
    joblib.dump(model, 'model/energy_model.pkl')

    def predict_consumption(input_data):
        model = joblib.load('model/energy_model.pkl')
        prediction = model.predict([input_data])
        return prediction[0]