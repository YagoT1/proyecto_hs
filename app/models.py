from app import db
from flask_login import UserMixin
from datetime import datetime
from app import db
from flask_login import current_user

class User(db.Model, UserMixin):
    registros = db.relationship('Registro', backref='usuario', lazy=True)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    
class Registro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False)
    horas = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(10), nullable=False)
    observacion = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Registro {self.fecha} - {self.horas} hs - {self.tipo}>"