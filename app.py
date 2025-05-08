from flask import Flask, render_template, request
from model import predict_consumption
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    if request.method == 'POST':

        #Obtener datos del formulario
        area = float(request.form['area'])
        occupancy = float(request.form['occupancy'])
        day = int(request.fomr['day_of_week'])
        hour = int(request.form['hour_of_day'])

        #Realizar la prediccion
        input_data = [area, occupancy, day_of_week, hour_of_day]
        prediction = predict_consumption(input_data)

    return render_template('index.html', prediction=prediction)

__name__ = '__main__'
app.run(debug=True)