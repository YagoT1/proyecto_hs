import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from fpdf import FPDF
from dotenv import load_dotenv
from datetime import date
from io import BytesIO

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_segura_por_defecto")

# Función para detectar domingos
def es_dia_100(dia):
    fecha = date(date.today().year, date.today().month, dia)
    return fecha.weekday() == 6  # 6 = domingo

@app.route("/", methods=["GET", "POST"])
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
                tipo = "100%" if feriado or es_dia_100(dia) else "50%"
                datos.append((dia, horas, tipo, obs))

        if not datos:
            flash("No se ingresaron horas válidas.", "error")
            return redirect(url_for("index"))

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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
