# proyecto_hs/app/models.py

from app import db # Importa 'db' desde el paquete 'app' (donde se inicializó)
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    # Nombre de la tabla en la base de datos.
    # Si tu tabla de usuarios existente se llama 'users' (en plural), cámbialo a '__tablename__ = 'users''
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128)) # Almacena el hash de la contraseña

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class Registro(db.Model):
    __tablename__ = 'registros' # Nombre de la tabla para los registros de horas

    id = db.Column(db.Integer, primary_key=True)
    # user_id es una clave foránea que referencia el 'id' de la tabla 'user'
    # ASEGÚRATE de que 'user.id' coincide con el __tablename__ de tu clase User.
    # Si tu tabla User es 'users', esto debería ser db.ForeignKey('users.id')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)  # Ej. "50%" o "100%"
    observacion = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Fecha y hora de creación del registro

    # Define la relación con el modelo User
    # 'User' aquí se refiere a la clase Python User, no al nombre de la tabla
    user = db.relationship('User', backref='registros')

    def __repr__(self):
        return f"Registro('{self.fecha}', '{self.horas}', '{self.tipo}')"