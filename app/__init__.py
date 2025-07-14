import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Cargar variables de entorno desde .env.
    # Es crucial que esto se ejecute antes de cualquier configuración que dependa de ellas.
    load_dotenv() 

    instance_path = os.path.join(app.root_path, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)

    app.secret_key = os.getenv("SECRET_KEY", "clave_segura_por_defecto")

    # Obtener la URL de la base de datos de las variables de entorno
    db_url = os.getenv("DATABASE_URL")

    # --- DEPURACIÓN CRÍTICA: Imprimir la URL de la base de datos obtenida ---
    print(f"DEBUG: Valor de DATABASE_URL obtenido de .env: {db_url}")
    # ----------------------------------------------------------------------

    if not db_url:
        # Si DATABASE_URL no está configurada, lanzamos un error explícito.
        # Esto asegura que no haya un fallback silencioso a SQLite.
        raise RuntimeError("La variable de entorno DATABASE_URL no está configurada. Por favor, asegúrate de que tu archivo .env contiene 'DATABASE_URL=\"postgresql://...\"'.")
    
    # Verificar que la URL de la base de datos apunta a PostgreSQL
    if not db_url.startswith("postgresql://"):
        raise ValueError(f"DATABASE_URL configurada no es una URL de PostgreSQL válida: {db_url}. Debe comenzar con 'postgresql://'.")

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- DEPURACIÓN FINAL: Imprimir la URI de SQLAlchemy configurada ---
    print(f"DEBUG: SQLALCHEMY_DATABASE_URI configurada a: {app.config['SQLALCHEMY_DATABASE_URI']}")
    # ------------------------------------------------------------------

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Importa modelos aquí para evitar importaciones circulares
    from app.models import User, Registro # Asegúrate de que Registro también esté importado

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registra blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)

    return app
