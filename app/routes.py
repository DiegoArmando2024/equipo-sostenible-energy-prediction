from flask import Blueprint, render_template, request
from model.predictor import predict_energy

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    if request.method == 'POST':
        area = float(request.form['area'])
        people = int(request.form['people'])
        day = int(request.form['day'])
        hour = int(request.form['hour'])
        prediction = predict_energy([[area, people, day, hour]])
    return render_template('index.html', prediction=prediction)
