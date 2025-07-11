import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    app = Flask(__name__)

    # Crear carpeta instance si no existe
    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    # Configuración básica
    app.secret_key = os.getenv("SECRET_KEY", "clave_segura_por_defecto")

    # Ruta absoluta para la base de datos SQLite dentro de instance
    db_path = os.getenv("DATABASE_URL")
    if not db_path:
        # Si no está en .env, usar ruta por defecto
        db_path = f"sqlite:///{os.path.join(instance_path, 'users.db')}"
    else:
        # Si viene con sqlite:/// relativo, convertirlo a absoluto para evitar problemas
        if db_path.startswith("sqlite:///"):
            relative_path = db_path.replace("sqlite:///", "")
            abs_path = os.path.join(app.root_path, relative_path)
            db_path = f"sqlite:///{abs_path}"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar extensiones con la app
    db.init_app(app)
    login_manager.init_app(app)

    # Importar modelos aquí para evitar errores de importación circular
    from app.models import User

    # Cargar usuario para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    return app
