# energia_app/blueprints/buildings.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from energia_app.forms import BuildingForm
from energia_app.models.user import Building, Prediction, db

buildings_bp = Blueprint('buildings', __name__, url_prefix='/buildings')

@buildings_bp.route('/', methods=['GET', 'POST'])
@buildings_bp.route('/<int:building_id>', methods=['GET'])
@login_required
def manage(building_id=None):
    form = BuildingForm()
    
    if building_id:
        building = Building.query.get_or_404(building_id)
        if request.method == 'GET':
            form.id.data = building.id
            form.name.data = building.name
            form.area.data = building.area
            form.location.data = building.location
            form.description.data = building.description
            form.active.data = building.active
    
    if form.validate_on_submit():
        if form.id.data and int(form.id.data) > 0:
            building = Building.query.get_or_404(int(form.id.data))
            building.name = form.name.data
            building.area = form.area.data
            building.location = form.location.data
            building.description = form.description.data
            building.active = form.active.data
            db.session.commit()
            flash(f'Edificio "{building.name}" actualizado correctamente.')
        else:
            new_building = Building(
                name=form.name.data,
                area=form.area.data,
                location=form.location.data,
                description=form.description.data,
                active=form.active.data
            )
            db.session.add(new_building)
            db.session.commit()
            flash(f'Edificio "{new_building.name}" registrado correctamente.')
        return redirect(url_for('buildings.manage'))
    
    buildings = Building.query.order_by(Building.name).all()
    return render_template('buildings/manage.html', form=form, buildings=buildings)

@buildings_bp.route('/delete/<int:building_id>')
@login_required
def delete(building_id):
    if current_user.role != 'admin':
        flash('No tienes permisos para eliminar edificios.')
        return redirect(url_for('buildings.manage'))
    
    building = Building.query.get_or_404(building_id)
    name = building.name
    
    if Prediction.query.filter_by(building_id=building_id).count() > 0:
        flash(f'No se puede eliminar el edificio "{name}" porque tiene predicciones asociadas.')
        return redirect(url_for('buildings.manage'))
    
    db.session.delete(building)
    db.session.commit()
    flash(f'Edificio "{name}" eliminado correctamente.')
    return redirect(url_for('buildings.manage'))