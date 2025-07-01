# proyecto_hs/app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, FloatField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from app.models import User # Importa el modelo User desde la nueva ubicación

# Formulario de Registro de Usuarios
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    # Validaciones personalizadas para username y email
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está tomado. Por favor, elige uno diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese email ya está registrado. Por favor, elige uno diferente o inicia sesión.')

# Formulario de Inicio de Sesión
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me') # Opción para recordar sesión
    submit = SubmitField('Login')

# Formulario para Registrar Horas Extra
class RegistroForm(FlaskForm):
    fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()]) # Formato YYYY-MM-DD
    horas = FloatField('Horas', validators=[DataRequired(), NumberRange(min=0.1, max=24, message="Las horas deben ser entre 0.1 y 24.")])
    tipo = SelectField('Tipo de Hora Extra', choices=[('50%', '50%'), ('100%', '100%')], validators=[DataRequired()])
    observacion = StringField('Observación (opcional)', validators=[Length(max=200, message="La observación no puede exceder los 200 caracteres.")])
    submit = SubmitField('Registrar Horas')