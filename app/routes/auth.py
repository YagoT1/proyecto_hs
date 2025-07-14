from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User # Asegúrate de que tu modelo User esté correctamente definido
# Importa tus formularios de WTForms
from app.forms import LoginForm, RegistrationForm # <--- ¡Asegúrate de que estas importaciones sean correctas!
from datetime import date # Necesario para current_year en render_template
from fpdf import FPDF # Asegúrate de importar FPDF
from io import BytesIO # Asegúrate de importar BytesIO

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm() # <--- Instancia el formulario de Login aquí
    if form.validate_on_submit(): # <--- Usa validate_on_submit()
        username = form.username.data # <--- Accede a los datos a través del formulario
        password = form.password.data

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Usuario no registrado.", "error")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):
            flash("Contraseña incorrecta.", "error")
            return redirect(url_for("auth.login"))

        # Esta línea es la que hace que el botón "Recordarme" funcione
        login_user(user, remember=form.remember_me.data) # <--- Pasa remember_me
        flash("¡Has iniciado sesión con éxito!", "success")
        return redirect(url_for("main.index"))

    # Pasa el formulario a la plantilla para renderizar
    return render_template("auth/login.html", form=form, current_year=date.today().year)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm() # <--- Instancia el formulario de Registro aquí
    if form.validate_on_submit(): # <--- Usa validate_on_submit()
        username = form.username.data # <--- Accede a los datos a través del formulario
        email = form.email.data # Asumiendo que tu RegistrationForm tiene un campo 'email'
        password = form.password.data

        # La validación de unicidad de usuario/email ya debería estar en tu RegistrationForm (validate_username, validate_email)
        # y se maneja con form.validate_on_submit()

        hashed_password = generate_password_hash(password)
        # Asegúrate de que tu modelo User acepte email si lo estás usando
        new_user = User(username=username, email=email, password=hashed_password) # Ajusta si tu User no tiene email
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception as e: # Captura la excepción para depuración
            db.session.rollback()
            flash(f"Error al crear el usuario: {e}. Intente nuevamente.", "error")
            print(f"ERROR: Fallo al crear usuario en DB: {e}") # Para depuración en consola
            return redirect(url_for("auth.register"))

        flash("Usuario registrado correctamente. ¡Ahora puedes iniciar sesión!", "success")
        return redirect(url_for("auth.login"))

    # Pasa el formulario a la plantilla para renderizar
    return render_template("auth/register.html", form=form, current_year=date.today().year)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("auth.login"))

