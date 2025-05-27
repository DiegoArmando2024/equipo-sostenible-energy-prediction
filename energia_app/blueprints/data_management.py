# energia_app/blueprints/data_management.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, send_from_directory, Response
from flask_login import login_required, current_user
import os
import io
import csv
import pandas as pd
from werkzeug.utils import secure_filename
from energia_app.forms import EnergyDataForm
from energia_app.models.energy_data import EnergyData
from energia_app.models.model import Energy_Model
from energia_app.models.preprocess import preprocess_data
from energia_app.models.user import db, Building

data_bp = Blueprint('data', __name__, url_prefix='/data-management')

@data_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta página.')
        return redirect(url_for('dashboard.index'))
    
    manual_form = EnergyDataForm()
    buildings = Building.query.filter_by(active=True).all()
    manual_form.building_id.choices = [(0, 'Seleccione un edificio (opcional)')] + [(b.id, b.name) for b in buildings]
    
    energy_data = EnergyData.query.order_by(EnergyData.timestamp.desc()).limit(10).all()
    total_manual_records = EnergyData.query.count()
    
    dataset_stats = None
    if total_manual_records > 0:
        try:
            data_df = EnergyData.export_to_df()
            dataset_stats = {
                'n_samples': len(data_df),
                'area_min': data_df['area_edificio'].min(),
                'area_max': data_df['area_edificio'].max(),
                'consumo_min': data_df['consumo_energetico'].min(),
                'consumo_max': data_df['consumo_energetico'].max(),
                'consumo_mean': data_df['consumo_energetico'].mean()
            }
            
            if len(data_df) >= 10:
                correlaciones = {
                    'area_consumo': data_df['area_edificio'].corr(data_df['consumo_energetico']),
                    'ocupacion_consumo': data_df['ocupacion'].corr(data_df['consumo_energetico']),
                    'dia_consumo': data_df['dia_semana'].corr(data_df['consumo_energetico']),
                    'hora_consumo': data_df['hora_dia'].corr(data_df['consumo_energetico'])
                }
                dataset_stats['correlaciones'] = correlaciones
        except Exception as e:
            flash(f"Error al calcular estadísticas: {str(e)}")
    
    if request.method == 'POST' and manual_form.validate_on_submit():
        try:
            new_data = EnergyData(
                area_edificio=manual_form.area_edificio.data,
                ocupacion=manual_form.ocupacion.data,
                dia_semana=manual_form.dia_semana.data,
                hora_dia=manual_form.hora_dia.data,
                consumo_energetico=manual_form.consumo_energetico.data
            )
            
            if manual_form.building_id.data and manual_form.building_id.data > 0:
                new_data.building_id = manual_form.building_id.data
            
            db.session.add(new_data)
            db.session.commit()
            flash('Registro guardado correctamente.')
            return redirect(url_for('data.manage'))
        except Exception as e:
            flash(f'Error al guardar el registro: {str(e)}')
    
    return render_template(
        'data/manage.html',
        manual_form=manual_form,
        energy_data=energy_data,
        dataset_stats=dataset_stats,
        total_manual_records=total_manual_records,
        buildings_data=[{'id': b.id, 'name': b.name, 'area': b.area} for b in buildings]
    )

@data_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('dashboard.index'))
    
    if 'file' not in request.files:
        flash('No se ha seleccionado ningún archivo')
        return redirect(url_for('data.manage'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se ha seleccionado ningún archivo')
        return redirect(url_for('data.manage'))
    
    if file and allowed_file(file.filename):
        try:
            data = pd.read_csv(file)
            required_cols = ['area_edificio', 'ocupacion', 'dia_semana', 'hora_dia', 'consumo_energetico']
            missing_cols = [col for col in required_cols if col not in data.columns]
            
            if missing_cols:
                flash(f'El archivo CSV no tiene las columnas requeridas: {", ".join(missing_cols)}')
                return redirect(url_for('data.manage'))
            
            count = EnergyData.import_from_df(data)
            flash(f'Se han importado {count} registros correctamente a la base de datos.')
            
            if 'retrain' in request.form and request.form['retrain'] == 'yes':
                try:
                    all_data = EnergyData.export_to_df()
                    X, y = preprocess_data(all_data, training=True)
                    model = EnergyModel()
                    metrics = model.train(X, y)
                    flash(f'Modelo reentrenado con éxito. R² = {metrics["r2"]:.4f}')
                except Exception as e:
                    flash(f'Error al reentrenar el modelo: {str(e)}')
            
            return redirect(url_for('data.manage'))
        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}')
    else:
        flash('Tipo de archivo no permitido. Por favor, sube un archivo CSV.')
    
    return redirect(url_for('data.manage'))

@data_bp.route('/export')
@login_required
def export():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('dashboard.index'))
    
    energy_data = EnergyData.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['id', 'timestamp', 'building_id', 'area_edificio', 'ocupacion', 
                     'dia_semana', 'hora_dia', 'consumo_energetico'])
    
    for data in energy_data:
        writer.writerow([
            data.id,
            data.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            data.building_id,
            data.area_edificio,
            data.ocupacion,
            data.dia_semana,
            data.hora_dia,
            data.consumo_energetico
        ])
    
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=energy_data.csv"}
    )

@data_bp.route('/delete-all')
@login_required
def delete_all():
    if current_user.role != 'admin':
        flash('No tienes permisos para acceder a esta funcionalidad.')
        return redirect(url_for('dashboard.index'))
    
    try:
        EnergyData.query.delete()
        db.session.commit()
        flash('Todos los registros de datos energéticos han sido eliminados.')
    except Exception as e:
        flash(f'Error al eliminar los registros: {str(e)}')
    
    return redirect(url_for('data.manage'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@data_bp.route('/retrain', methods=['POST'])
@login_required
def retrain():
    """Reentrenar el modelo con todos los datos disponibles"""
    if current_user.role != 'admin':
        flash('No tienes permisos para reentrenar el modelo.')
        return redirect(url_for('data.manage'))
    
    try:
        # Obtener todos los datos de energía
        all_data = EnergyData.export_to_df()
        
        if len(all_data) < 10:
            flash('No hay suficientes datos para reentrenar el modelo (mínimo 10 registros).')
            return redirect(url_for('data.manage'))
        
        # Preprocesar los datos
        X, y = preprocess_data(all_data, training=True)
        
        # Crear y entrenar el modelo
        model = Energy_Model()
        metrics = model.train(X, y)
        
        flash(f'Modelo reentrenado exitosamente. R² = {metrics["r2"]:.4f}, RMSE = {metrics["rmse"]:.2f}')
        
    except Exception as e:
        flash(f'Error al reentrenar el modelo: {str(e)}')
    
    return redirect(url_for('data.manage'))