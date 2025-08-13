from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FloatField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, NumberRange
from app.models import User
from flask_wtf.file import FileField, FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Iniciar sesión')

class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige uno diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese email ya está registrado. Por favor, elige uno diferente.')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Solicitar Restablecimiento de Contraseña')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('No hay una cuenta con ese email. Debes registrarte primero.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nueva Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Nueva Contraseña', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Restablecer Contraseña')

class ErrorReportForm(FlaskForm):
    subject = StringField('Asunto del Reporte', validators=[DataRequired(), Length(min=5, max=100)])
    message = TextAreaField('Descripción del Error', validators=[DataRequired(), Length(min=10)])
    email = StringField('Tu Email (opcional)', validators=[Email()])
    submit = SubmitField('Enviar Reporte')

class RegistroForm(FlaskForm):
    fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    horas = FloatField('Horas Trabajadas', validators=[DataRequired(), NumberRange(min=0.1, max=24.0)])
    observacion = TextAreaField('Observación (Opcional)', validators=[Length(max=200)])
    submit = SubmitField('Guardar Registro')

# Formulario para edición de usuario por admin
class AdminEditUserForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    estado = BooleanField('Activo')  # Campo booleano para el estado (activo/inactivo)
    submit = SubmitField('Actualizar Usuario')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user and user.id != self.original_user_id:
            raise ValidationError('Ese nombre de usuario ya está en uso. Por favor, elige uno diferente.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user and user.id != self.original_user_id:
            raise ValidationError('Ese email ya está registrado. Por favor, elige uno diferente.')

    def __init__(self, original_user_id, *args, **kwargs):
        super(AdminEditUserForm, self).__init__(*args, **kwargs)
        self.original_user_id = original_user_id
