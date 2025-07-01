# proyecto_hs/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# Cargar variables de entorno (como SECRET_KEY, DATABASE_URL)
load_dotenv()

# Inicializa SQLAlchemy y Flask-Login sin una app específica por ahora
# (serán inicializados con la app en create_app())
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

def create_app():
    app = Flask(__name__)

    # Configuración de la aplicación
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')

    # Inicializa las extensiones de Flask con la instancia de la app
    db.init_app(app)
    login_manager.init_app(app)

    # IMPORTANTE: Importar los modelos *después* de que 'db' se ha inicializado con la app
    from app.models import User, Registro

    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar Blueprints
    from app.routes.auth import auth as auth_blueprint
    from app.routes.main import main as main_blueprint # ¡ASEGÚRATE DE QUE ESTA LÍNEA ESTÁ PRESENTE!

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)

    return app