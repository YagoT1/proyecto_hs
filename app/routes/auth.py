from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User
from app.forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm
from app.email import send_reset_email
from datetime import datetime
from pytz import timezone
import pytz
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if user and user.check_password(form.password.data):
            # 🚫 Verificar si el usuario está activo
            if not user.is_active:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'warning')
                return redirect(url_for('auth.login'))

            # ✅ Login exitoso
            login_user(user, remember=form.remember_me.data)

            # Actualizar la última conexión
            user.last_login = datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
            db.session.commit()

            next_page = request.args.get('next')

            if user.is_admin or user.is_owner or user.is_moderator:
                return redirect(url_for('admin.admin_dashboard'))

            return redirect(next_page) if next_page else redirect(url_for('main.index'))

        else:
            flash('Credenciales inválidas. Intente nuevamente.', 'danger')

    return render_template('auth/login.html', title='Iniciar sesión', form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'info')
    return redirect(url_for('auth.login'))

@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard'))  # Cambiado

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('¡Tu cuenta ha sido creada! Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard'))  # Cambiado

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash('Se ha enviado un correo electrónico con instrucciones para restablecer su contraseña.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('No se encontró una cuenta con ese correo electrónico.', 'danger')
    return render_template('auth/reset_request.html', form=form)

@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_dashboard'))  # Cambiado

    user = User.verify_reset_token(token)
    if not user:
        flash('El token es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Su contraseña ha sido actualizada. Ya puede iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_token.html', form=form, token=token)
