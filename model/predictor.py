import joblib
import os

model_path = os.path.join(os.path.dirname(__file__), 'energy_model.pkl')
model = joblib.load(model_path)

def predict_energy(input_data):
    return model.predict(input_data)[0]
