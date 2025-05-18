from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, FloatField, TextAreaField, SelectField, SelectMultipleField, IntegerField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
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
    buildings = SelectMultipleField('Edificios', coerce=int, 
                                   validators=[DataRequired(message="Seleccione al menos un edificio")])
    ocupacion = IntegerField('Nivel de ocupación (personas)', 
                             validators=[DataRequired(), NumberRange(min=0, max=1000)])
    dia_semana = SelectField('Día de la semana', coerce=int, choices=[
        (0, 'Lunes'), (1, 'Martes'), (2, 'Miércoles'),
        (3, 'Jueves'), (4, 'Viernes'), (5, 'Sábado'), (6, 'Domingo')
    ], validators=[DataRequired()])
    hora_dia = SelectField('Hora del día', coerce=int, choices=[
        (h, f'{h}:00') for h in range(24)
    ], validators=[DataRequired()])
    submit = SubmitField('Predecir consumo')