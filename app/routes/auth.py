from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User

auth_bp = Blueprint('auth', __name__)  # No template_folder aquí

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Por favor complete todos los campos.", "error")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for("auth.login"))

        if not check_password_hash(user.password, password):
            flash("Contraseña incorrecta.", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("main.index"))

    return render_template("auth/login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Por favor complete todos los campos.", "error")
            return redirect(url_for("auth.register"))

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("El nombre de usuario ya existe.", "error")
            return redirect(url_for("auth.register"))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("Error al crear el usuario. Intente nuevamente.", "error")
            return redirect(url_for("auth.register"))

        flash("Usuario registrado correctamente.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
