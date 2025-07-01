import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# Extensiones
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuración básica
    app.secret_key = os.getenv("SECRET_KEY", "clave_segura_por_defecto")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///users.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)

    # Importar modelos aquí para evitar errores de importación circular
    from app.models import User

    # Cargar usuario para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar Blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    return app
