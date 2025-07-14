from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField, IntegerField, SelectField, TextAreaField, FloatField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from app.models import User # Asegúrate de que tu modelo User esté importado
import re # Importa re para expresiones regulares
from flask_login import current_user # Necesario para la validación de unicidad en UpdateAccountForm

# Validador personalizado para la fortaleza de la contraseña
class PasswordStrength:
    def __init__(self, min_length=8, require_uppercase=True, require_lowercase=True, require_digit=True, require_special=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special

    def __call__(self, form, field):
        password = field.data

        if len(password) < self.min_length:
            raise ValidationError(f'La contraseña debe tener al menos {self.min_length} caracteres.')

        if self.require_uppercase and not re.search(r'[A-Z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')

        if self.require_lowercase and not re.search(r'[a-z]', password):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula.')

        if self.require_digit and not re.search(r'\d', password):
            raise ValidationError('La contraseña debe contener al menos un número.')

        # Caracteres especiales comunes. Puedes ajustar esta lista.
        if self.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValidationError('La contraseña debe contener al menos un carácter especial.')


# Formulario de Registro
class RegistrationForm(FlaskForm):
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Correo Electrónico',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Contraseña', validators=[
        DataRequired(),
        PasswordStrength(min_length=8, require_uppercase=True, require_lowercase=True, require_digit=True, require_special=True)
    ])
    confirm_password = PasswordField('Confirmar Contraseña',
                                     validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden.')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        # Validación existente de unicidad
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Ese nombre de usuario ya está tomado. Por favor, elige uno diferente.')

        # Validación para palabras reservadas en el nombre de usuario
        username_lower = username.data.lower()
        reserved_words = ['admin', 'administrador', 'root', 'superuser', 'moderator'] # Puedes añadir más
        for word in reserved_words:
            if word in username_lower:
                raise ValidationError(f'El nombre de usuario no puede contener palabras reservadas como "{word}".')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Ese correo electrónico ya está registrado. Por favor, elige uno diferente.')

# Formulario de Inicio de Sesión
class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')

# Formulario para Registrar Horas (individual)
class RegistroForm(FlaskForm):
    fecha = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    horas = IntegerField('Horas', validators=[DataRequired(), NumberRange(min=0, max=24)])
    tipo = SelectField('Tipo de Hora Extra', choices=[('50%', '50%'), ('100%', '100%')], validators=[DataRequired()])
    observacion = TextAreaField('Observaciones (opcional)', validators=[Length(max=200)])
    submit = SubmitField('Registrar Horas')

# Formulario para Actualizar Cuenta de Usuario (Perfil)
class UpdateAccountForm(FlaskForm):
    username = StringField('Nombre de Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Correo Electrónico',
                        validators=[DataRequired(), Email()])
    submit = SubmitField('Actualizar Cuenta')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateAccountForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Ese nombre de usuario ya está tomado. Por favor, elige uno diferente.')
        
        # Nueva validación para palabras reservadas al actualizar (opcional, pero recomendado)
        username_lower = username.data.lower()
        reserved_words = ['admin', 'administrador', 'root', 'superuser', 'moderator']
        for word in reserved_words:
            if word in username_lower:
                raise ValidationError(f'El nombre de usuario no puede contener palabras reservadas como "{word}".')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Ese correo electrónico ya está registrado. Por favor, elige uno diferente.')

# Nuevo Formulario para Restablecer Contraseña (desde Admin)
class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(),
        PasswordStrength(min_length=8, require_uppercase=True, require_lowercase=True, require_digit=True, require_special=True)
    ])
    confirm_new_password = PasswordField('Confirmar Nueva Contraseña',
                                         validators=[DataRequired(), EqualTo('new_password', message='Las contraseñas no coinciden.')])
    submit = SubmitField('Restablecer Contraseña')

# Nuevo Formulario para la verificación de Recibos
class VerifyRecibosForm(FlaskForm):
    legajo = StringField('Legajo (Nombre de Usuario)', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Verificar Acceso')

# NUEVO Formulario para los metadatos del recibo de sueldo
class ReciboMetaDataForm(FlaskForm):
    categoria = StringField('Categoría', validators=[Optional(), Length(max=100)])
    lugar_entrega = StringField('Lugar de Entrega (Sector)', validators=[Optional(), Length(max=100)])
    cargo = StringField('Cargo', validators=[Optional(), Length(max=100)])
    liquido_a_pagar = FloatField('Líquido a Pagar', validators=[Optional(), NumberRange(min=0)])
    tipo_liquidacion = SelectField('Tipo de Liquidación', 
                                   choices=[('Normal', 'Normal'), ('Extra', 'Extra')], 
                                   validators=[Optional()])
    submit = SubmitField('Guardar Metadatos del Recibo')

