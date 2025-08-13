import os
import sys
import logging
from datetime import datetime

from flask import Flask
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from config import Config

login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

mail = Mail()
db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'una-clave-secreta-muy-larga-y-aleatoria-para-produccion')
        app.logger.debug(f"SECRET_KEY por defecto aplicada: {app.config['SECRET_KEY']}")

    login_manager.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    @app.before_request
    def before_request():
        if current_user.is_authenticated:
            try:
                current_user.last_seen = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al actualizar last_seen para {current_user.username}: {e}")
            # db.session.remove() NO DEBE ESTAR AQUÍ. Flask-SQLAlchemy lo maneja automáticamente.

    if not app.debug and not app.testing:
        app.logger.setLevel(logging.DEBUG)

    from app.routes.main import main
    app.register_blueprint(main)

    from app.routes.auth import auth as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.routes.admin import admin as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app

__all__ = ['db', 'bcrypt', 'mail', 'login_manager', 'csrf']
