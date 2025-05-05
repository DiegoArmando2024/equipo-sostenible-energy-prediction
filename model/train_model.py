import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import numpy as np
import os

# Datos sintéticos
np.random.seed(0)
data = pd.DataFrame({
    'area': np.random.randint(50, 500, 100),
    'people': np.random.randint(1, 100, 100),
    'day': np.random.randint(0, 7, 100),
    'hour': np.random.randint(0, 24, 100),
})
data['consumption'] = (data['area'] * 0.5 + data['people'] * 2 + data['hour'] * 1.5 + data['day'] * 0.8) + np.random.normal(0, 10, 100)

# Entrenamiento
X = data[['area', 'people', 'day', 'hour']]
y = data['consumption']

model = LinearRegression()
model.fit(X, y)

# Guardar modelo
os.makedirs("model", exist_ok=True)
joblib.dump(model, 'model/energy_model.pkl')
data.to_csv("data/synthetic_data.csv", index=False)
