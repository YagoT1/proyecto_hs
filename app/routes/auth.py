# proyecto_hs/app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db # Importa 'db' desde el paquete 'app'
from app.models import User # Importa el modelo User desde 'app.models'
from app.forms import LoginForm, RegistrationForm # Importa los formularios desde 'app.forms'

# Define el Blueprint para autenticación.
# El 'url_prefix=/auth' significa que todas las rutas aquí comenzarán con /auth (ej. /auth/login)
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # Si el usuario ya está autenticado, redirige al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) # Asume que 'main' es el nombre del Blueprint del dashboard
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data) # Hashea la contraseña
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login')) # Redirige a la página de login
    return render_template('register.html', title='Registrarse', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya está autenticado, redirige al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Verifica si el usuario existe y si la contraseña es correcta
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data) # Inicia sesión al usuario
            # Redirige al usuario a la página a la que intentaba acceder antes del login,
            # o al dashboard si no había una página anterior.
            next_page = request.args.get('next')
            flash('¡Inicio de sesión exitoso!', 'success')
            return redirect(next_page or url_for('main.dashboard'))
        else:
            flash('Inicio de sesión fallida. Por favor, verifica tu usuario y contraseña.', 'danger')
    return render_template('login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
@login_required # Esta ruta solo es accesible si el usuario está logueado
def logout():
    logout_user() # Cierra la sesión del usuario
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('auth.login')) # Redirige a la página de login