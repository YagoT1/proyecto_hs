from flask import Flask, render_template, request, send_file, flash
from fpdf import FPDF
from datetime import datetime
import io
import locale

app = Flask(__name__)
app.secret_key = 'clave_segura_para_mensajes_flash'  # Reemplazar con una clave segura

# Localización en español (ajustar si estás en Windows)
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
    except:
        pass  # Usa inglés si no se puede cambiar

@app.route("/", methods=["GET", "POST"])
def index():
    hoy = datetime.today()
    dia_actual = hoy.day
    mes_actual = hoy.month
    anio = hoy.year

    nombre_mes = hoy.strftime("%B").capitalize()
    horas_extra = []
    total_50 = 0
    total_100 = 0

    if request.method == "POST":
        feriados = request.form.getlist("feriados[]")
        feriados = [int(f) for f in feriados]

        for dia in range(1, dia_actual + 1):
            horas_input = request.form.get(f"horas_{dia}")
            observacion = request.form.get(f"obs_{dia}", "").strip()

            if not horas_input:
                continue

            try:
                horas = float(horas_input)
                if horas < 0 or horas > 24:
                    raise ValueError
            except ValueError:
                flash(f"Error en el ingreso del día {dia}: Ingrese un valor numérico válido entre 0 y 24 hs.", "error")
                return render_template("form.html", dia_hoy=dia_actual)

            if datetime(anio, mes_actual, dia).weekday() == 6 or dia in feriados:
                tipo = "100%"
                total_100 += horas
            else:
                tipo = "50%"
                total_50 += horas

            horas_extra.append((dia, horas, tipo, observacion))

        if not horas_extra:
            flash("No se ingresaron horas válidas para generar el PDF.", "error")
            return render_template("form.html", dia_hoy=dia_actual)

        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Reporte de Horas Extra - {nombre_mes} {anio}", ln=True, align="C")
        pdf.ln(10)

        for dia, horas, tipo, obs in horas_extra:
            linea = f"{dia:02d} - {horas:.2f} hs - {tipo} - {obs}"
            pdf.cell(200, 10, txt=linea, ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", style='B', size=12)
        pdf.cell(200, 10, txt=f"Total horas al 50%: {total_50:.2f}", ln=True)
        pdf.cell(200, 10, txt=f"Total horas al 100%: {total_100:.2f}", ln=True)

        pdf_bytes = pdf.output(dest='S').encode('latin1')
        pdf_output = io.BytesIO(pdf_bytes)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            as_attachment=True,
            download_name='horas_extra.pdf',
            mimetype='application/pdf'
        )

    return render_template("form.html", dia_hoy=dia_actual)

if __name__ == "__main__":
    app.run(debug=True)
