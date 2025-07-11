from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from fpdf import FPDF
from flask_login import login_required
from flask_login import current_user
from datetime import date
from io import BytesIO
from app.forms import RegistroForm
from app.models import Registro
from app import db

# Define el Blueprint con el nombre 'main'
main_bp = Blueprint('main', __name__)

@main_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    hoy = date.today()
    dias_del_mes = hoy.day
    datos = []

    if request.method == "POST":
        for dia in range(1, dias_del_mes + 1):
            horas = request.form.get(f"horas_{dia}")
            obs = request.form.get(f"obs_{dia}", "")
            feriado = f"feriado_{dia}" in request.form

            if horas:
                tipo = "100%" if feriado or date(hoy.year, hoy.month, dia).weekday() == 6 else "50%"
                datos.append((dia, horas, tipo, obs))

        if not datos:
            flash("No se ingresaron horas válidas.", "error")
            return redirect(url_for("main.index"))

        # Generar PDF en memoria
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Horas Extra - {hoy.strftime('%B %Y')}", ln=1, align='C')
        pdf.ln(5)

        for dia, horas, tipo, obs in datos:
            linea = f"Día {dia} - {horas} hs - {tipo}"
            if obs:
                linea += f" - {obs}"
            pdf.cell(200, 10, txt=linea, ln=1)

        output = BytesIO()
        pdf.output(output)
        output.seek(0)

        filename = f"horas_extra_{hoy.month}_{hoy.year}.pdf"
        return send_file(output, download_name=filename, as_attachment=True)

    return render_template("index.html", dias=dias_del_mes)

@main_bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_horas():
    form = RegistroForm()
    if form.validate_on_submit():
        nuevo_registro = Registro(
            fecha=form.fecha.data,
            horas=form.horas.data,
            tipo=form.tipo.data,
            observacion=form.observacion.data,
            user_id=current_user.id
        )
        db.session.add(nuevo_registro)
        db.session.commit()
        flash("Horas extra registradas con éxito.", "success")
        return redirect(url_for("main.index"))
    # Asegúrate de que la plantilla 'main/registrar_horas.html' exista
    return render_template("main/registrar_horas.html", form=form)

# Nueva ruta para el historial
@main_bp.route('/historial')
@login_required # Si esta ruta requiere que el usuario esté logueado
def historial():
    # Aquí puedes recuperar los registros del usuario actual desde la base de datos
    # Por ejemplo:
    # registros = Registro.query.filter_by(user_id=current_user.id).order_by(Registro.fecha.desc()).all()
    # return render_template("historial.html", registros=registros)

    # Por ahora, solo renderiza la plantilla.
    # Asegúrate de que la plantilla 'historial.html' exista en tu carpeta 'templates'.
    return render_template("historial.html")
