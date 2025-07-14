from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_moderator = db.Column(db.Boolean, default=False, nullable=False)
    is_owner = db.Column(db.Boolean, default=False, nullable=False)
    registros = db.relationship('Registro', backref='author', lazy=True)
    recibos = db.relationship('Recibo', backref='uploader', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', 'Admin: {self.is_admin}', 'Moderator: {self.is_moderator}', 'Owner: {self.is_owner}')"

class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    observacion = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Registro('{self.fecha}', '{self.horas}', '{self.tipo}', '{self.user_id}')"

class Recibo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Nuevos campos para los metadatos del recibo
    categoria = db.Column(db.String(100), nullable=True)
    lugar_entrega = db.Column(db.String(100), nullable=True)
    cargo = db.Column(db.String(100), nullable=True)
    liquido_a_pagar = db.Column(db.Float, nullable=True) # Usamos Float para valores monetarios
    tipo_liquidacion = db.Column(db.String(50), nullable=True) # Ej: 'Normal', 'Extra'

    def __repr__(self):
        return f"Recibo('{self.filename}', '{self.upload_date}', 'User: {self.user_id}', 'Cat: {self.categoria}', 'Liq: {self.liquido_a_pagar}')"

