from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, TextAreaField, SelectField, SelectMultipleField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange, Optional
from energia_app.models.user import User, Building

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField(
        'Repetir Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Por favor usa un nombre de usuario diferente.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Por favor usa una dirección de email diferente.')

class BuildingForm(FlaskForm):
    id = HiddenField('ID', default=0)
    name = StringField('Nombre del Edificio', validators=[DataRequired(), Length(min=2, max=100)])
    area = FloatField('Área (m²)', validators=[DataRequired(), NumberRange(min=1, message="El área debe ser mayor a 1 m²")])
    location = StringField('Ubicación', validators=[Length(max=150)])
    description = TextAreaField('Descripción', validators=[Length(max=500)])
    active = BooleanField('Activo', default=True)
    submit = SubmitField('Guardar')
    
    def validate_name(self, name):
        # Solo validar nombres duplicados en caso de creación (no edición)
        building_id = self.id.data
        if not building_id or int(building_id) <= 0:
            building = Building.query.filter_by(name=name.data).first()
            if building is not None:
                raise ValidationError('Ya existe un edificio con este nombre.')

class PredictionForm(FlaskForm):
    """Formulario para realizar predicciones de consumo energético"""
    
    buildings = SelectMultipleField('Edificios', coerce=int, 
                                   validators=[DataRequired(message="Seleccione al menos un edificio")],
                                   render_kw={"class": "form-select"})
    
    ocupacion = IntegerField('Nivel de ocupación (personas)',
                            validators=[DataRequired(message="Ingrese un nivel de ocupación"),
                                       NumberRange(min=1, message="La ocupación debe ser al menos 1")],
                            default=50,
                            render_kw={"class": "form-control"})
    
    # Cambiamos los valores para que empiecen en 1 en lugar de 0
    dia_semana = SelectField('Día de la semana',
                           choices=[(1, 'Lunes'), (2, 'Martes'), (3, 'Miércoles'), 
                                   (4, 'Jueves'), (5, 'Viernes'), (6, 'Sábado'), (7, 'Domingo')],
                           validators=[DataRequired(message="Seleccione un día de la semana")],
                           coerce=int,
                           default=1,  # Lunes = 1 ahora
                           render_kw={"class": "form-select"})
    
    # Cambiamos las horas para que empiecen en 1 en lugar de 0
    hora_dia = SelectField('Hora del día',
                         choices=[(i+1, f"{i:02d}:00") for i in range(24)],  # i+1 para valores, pero mostramos 00:00, 01:00, etc.
                         validators=[DataRequired(message="Seleccione una hora del día")],
                         coerce=int,
                         default=1,  # 00:00 = 1 ahora
                         render_kw={"class": "form-select"})
    
    submit = SubmitField('Predecir consumo', 
                         render_kw={"class": "btn btn-primary"})
    
class EnergyDataForm(FlaskForm):
    building_id = SelectField('Edificio', coerce=int, validators=[Optional()])
    area_edificio = FloatField('Área del edificio (m²)', validators=[DataRequired(), NumberRange(min=1)])
    ocupacion = IntegerField('Ocupación (personas)', validators=[DataRequired(), NumberRange(min=0)])
    dia_semana = SelectField('Día de la semana', coerce=int, choices=[
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')
    ], validators=[DataRequired()])
    hora_dia = SelectField('Hora del día', coerce=int, choices=[
        (h, f'{h}:00') for h in range(24)
    ], validators=[DataRequired()])
    consumo_energetico = FloatField('Consumo energético (kWh)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Guardar Registro')