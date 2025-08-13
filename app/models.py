from datetime import datetime
from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app

@login_manager.user_loader
def load_user(user_id):
    """
    Carga un usuario dado su ID.
    Requerido por Flask-Login.
    """
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    """
    Modelo de Usuario para la base de datos.
    """
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)
    is_moderator = db.Column(db.Boolean, default=False)
    is_owner = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # Campo nuevo para estado del usuario
    area = db.Column(db.String(120))  # Campo para el área del usuario
    last_seen = db.Column(db.DateTime, default=datetime.utcnow) # ¡NUEVA COLUMNA AÑADIDA!

    # Relaciones
    registros = db.relationship('Registro', backref='autor', lazy='dynamic')
    recibos = db.relationship('Recibo', backref='propietario', lazy='dynamic')

    def set_password(self, password):
        """Hashea y establece la contraseña del usuario."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña hasheada."""
        return check_password_hash(self.password_hash, password)

    def get_reset_token(self, expires_sec=1800):
        """
        Genera un token seguro para el restablecimiento de contraseña.
        El token expira en 30 minutos (1800 segundos).
        """
        secret_key_bytes = current_app.config['SECRET_KEY'].encode('utf-8')
        s = Serializer(secret_key_bytes, expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        """
        Verifica un token de restablecimiento de contraseña.
        """
        secret_key_bytes = current_app.config['SECRET_KEY'].encode('utf-8')
        s = Serializer(secret_key_bytes)
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f'<User {self.username}>'

class Registro(db.Model):
    """
    Modelo para los registros de horas trabajadas.
    """
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    observacion = db.Column(db.String(500))
    tipo = db.Column(db.String(50), default='normal')
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Registro {self.fecha} - {self.horas} horas por User {self.user_id}>'

class Recibo(db.Model):
    """
    Modelo para los recibos subidos por los usuarios.
    """
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False, unique=True)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Recibo {self.filename} por User {self.user_id}>'
