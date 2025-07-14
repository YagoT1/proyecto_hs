import os
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, abort, current_app, session
from fpdf import FPDF
from flask_login import login_required
from flask_login import current_user
from datetime import date, datetime, timedelta
from io import BytesIO
from werkzeug.utils import secure_filename # Importar secure_filename para nombres de archivo seguros
from app.forms import RegistroForm, UpdateAccountForm, ResetPasswordForm, VerifyRecibosForm # Asegúrate de que VerifyRecibosForm esté importado
from app.models import Registro, User, Recibo # Asegúrate de que User y Recibo estén importados
from app import db

# Define el Blueprint con el nombre 'main'
main_bp = Blueprint('main', __name__)

# Configuración para la carga de archivos (asegúrate de que esta carpeta exista)
UPLOAD_FOLDER = 'static/uploads/recibos'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'} # Tipos de archivo permitidos

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route("/", methods=["GET"]) # Solo GET para el dashboard
@login_required
def index():
    hoy = date.today()

    # Lógica para calcular el total de horas registradas para el usuario actual
    total_horas_registradas = 0
    if current_user.is_authenticated:
        # Obtener todos los registros del usuario actual
        registros_usuario = Registro.query.filter_by(user_id=current_user.id).all()
        # Sumar las horas de cada registro
        total_horas_registradas = sum(registro.horas for registro in registros_usuario)

        # --- DEBUGGING: Imprimir información para verificar si se están cargando los datos ---
        print(f"DEBUG: User ID: {current_user.id}")
        print(f"DEBUG: Registros encontrados para el usuario: {len(registros_usuario)}")
        print(f"DEBUG: Total Horas Registradas: {total_horas_registradas}")
        # ----------------------------------------------------------------------------------

    # Pasar el total de horas registradas y el año actual a la plantilla
    return render_template("index.html", total_horas_registradas=total_horas_registradas, current_year=hoy.year)

@main_bp.route("/registrar", methods=["GET", "POST"])
@login_required
def registrar_horas():
    if request.method == "POST":
        action = request.form.get('action') # Obtener la acción del botón presionado

        if action == 'save_records':
            registros_a_guardar = []
            
            # Iterar sobre los datos del formulario para encontrar las entradas dinámicas
            i = 0
            while True:
                fecha_str = request.form.get(f"fecha_{i}")
                horas_str = request.form.get(f"horas_{i}")
                obs = request.form.get(f"obs_{i}", "")
                feriado = f"feriado_{i}" in request.form

                if not fecha_str: # Si no hay fecha para este índice, significa que no hay más entradas
                    break

                # Validaciones básicas
                if not horas_str or not horas_str.isdigit():
                    flash(f"Error: Las horas para la entrada de la fecha {fecha_str} no son un número válido.", "error")
                    i += 1
                    continue

                try:
                    fecha_registro = date.fromisoformat(fecha_str)
                    horas_int = int(horas_str)
                except ValueError:
                    flash(f"Error: Formato de fecha u horas inválido para la entrada de la fecha {fecha_str}.", "error")
                    i += 1
                    continue
                
                tipo = "100%" if feriado or fecha_registro.weekday() == 6 else "50%"
                
                nuevo_registro = Registro(
                    fecha=fecha_registro,
                    horas=horas_int,
                    tipo=tipo,
                    observacion=obs,
                    user_id=current_user.id
                )
                registros_a_guardar.append(nuevo_registro)
                i += 1

            if not registros_a_guardar:
                flash("No se ingresaron registros válidos para guardar.", "error")
                return redirect(url_for("main.registrar_horas"))

            # --- Guardar los nuevos registros en la base de datos ---
            try:
                for registro in registros_a_guardar:
                    db.session.add(registro)
                db.session.commit()
                flash("Registros guardados con éxito.", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error al guardar los registros: {e}", "error")
                print(f"ERROR: Fallo al guardar en la DB: {e}")
            
            return redirect(url_for("main.index")) # Redirigir al dashboard después de guardar

        elif action == 'generate_pdf':
            # Generar PDF de *todos* los registros del usuario desde la base de datos
            registros_para_pdf = Registro.query.filter_by(user_id=current_user.id).order_by(Registro.fecha.asc()).all()

            if not registros_para_pdf:
                flash("No hay registros para generar el PDF.", "info")
                return redirect(url_for("main.registrar_horas"))

            # Calcular totales
            total_horas_generales = sum(r.horas for r in registros_para_pdf)
            total_horas_50 = sum(r.horas for r in registros_para_pdf if r.tipo == '50%')
            total_horas_100 = sum(r.horas for r in registros_para_pdf if r.tipo == '100%')

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Reporte de Horas Extra - {current_user.username}", ln=1, align='C')
            pdf.ln(5)

            for registro in registros_para_pdf:
                linea = f"Fecha: {registro.fecha.strftime('%d/%m/%Y')} - Horas: {registro.horas} hs - Tipo: {registro.tipo}"
                if registro.observacion:
                    linea += f" - Obs: {registro.observacion}"
                pdf.cell(0, 10, txt=linea, ln=1)
            
            # Añadir totales al PDF
            pdf.ln(10) # Salto de línea
            pdf.set_font("Arial", 'B', 12) # Negrita para los totales
            pdf.cell(0, 10, txt=f"Resumen de Horas:", ln=1)
            pdf.set_font("Arial", size=12) # Volver a normal
            pdf.cell(0, 10, txt=f"Total de Horas Registradas: {total_horas_generales} hs", ln=1)
            pdf.cell(0, 10, txt=f"Total Horas al 50%: {total_horas_50} hs", ln=1)
            pdf.cell(0, 10, txt=f"Total Horas al 100%: {total_horas_100} hs", ln=1)


            output = BytesIO()
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            output.write(pdf_bytes)
            output.seek(0)

            filename = f"reporte_horas_extra_{current_user.username}_{date.today().strftime('%Y%m%d')}.pdf"
            return send_file(output, download_name=filename, as_attachment=True)

    # Si es GET, o si el POST no es ninguna de las acciones definidas, renderiza el formulario
    return render_template("main/registrar_horas.html", current_year=date.today().year)

# Ruta para el historial de horas extra
@main_bp.route('/historial')
@login_required
def historial():
    registros = Registro.query.filter_by(user_id=current_user.id).order_by(Registro.fecha.desc()).all()
    return render_template("main/historial.html", registros=registros, current_year=date.today().year)

# Nueva ruta para generar PDF del historial completo
@main_bp.route('/generar_historial_pdf')
@login_required
def generar_historial_pdf():
    registros_para_pdf = Registro.query.filter_by(user_id=current_user.id).order_by(Registro.fecha.asc()).all()

    if not registros_para_pdf:
        flash("No hay registros en tu historial para generar el PDF.", "info")
        return redirect(url_for("main.historial"))

    # Calcular totales para el PDF del historial
    total_horas_generales = sum(r.horas for r in registros_para_pdf)
    total_horas_50 = sum(r.horas for r in registros_para_pdf if r.tipo == '50%')
    total_horas_100 = sum(r.horas for r in registros_para_pdf if r.tipo == '100%')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Reporte Completo de Horas Extra - {current_user.username}", ln=1, align='C')
    pdf.ln(5)

    for registro in registros_para_pdf:
        linea = f"Fecha: {registro.fecha.strftime('%d/%m/%Y')} - Horas: {registro.horas} hs - Tipo: {registro.tipo}"
        if registro.observacion:
                    linea += f" - Obs: {registro.observacion}"
        pdf.cell(0, 10, txt=linea, ln=1)
    
    # Añadir totales al PDF del historial
    pdf.ln(10) # Salto de línea
    pdf.set_font("Arial", 'B', 12) # Negrita para los totales
    pdf.cell(0, 10, txt=f"Resumen de Horas:", ln=1)
    pdf.set_font("Arial", size=12) # Volver a normal
    pdf.cell(0, 10, txt=f"Total de Horas Registradas: {total_horas_generales} hs", ln=1)
    pdf.cell(0, 10, txt=f"Total Horas al 50%: {total_horas_50} hs", ln=1)
    pdf.cell(0, 10, txt=f"Total Horas al 100%: {total_horas_100} hs", ln=1)

    output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    output.write(pdf_bytes)
    output.seek(0)

    filename = f"historial_horas_extra_{current_user.username}_{date.today().strftime('%Y%m%d')}.pdf"
    return send_file(output, download_name=filename, as_attachment=True)

# Ruta para editar un registro
@main_bp.route('/editar_registro/<int:registro_id>', methods=['GET', 'POST'])
@login_required
def edit_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)

    # Seguridad: Asegurarse de que el usuario actual sea el propietario del registro
    if registro.user_id != current_user.id:
        flash("No tienes permiso para editar este registro.", "error")
        abort(403) # Prohibido

    form = RegistroForm(obj=registro) # <--- Pre-llenar el formulario con los datos del registro

    if form.validate_on_submit():
        # Actualizar los datos del registro con los datos del formulario
        registro.fecha = form.fecha.data
        registro.horas = form.horas.data
        registro.tipo = form.tipo.data
        registro.observacion = form.observacion.data
        
        try:
            db.session.commit()
            flash("Registro actualizado con éxito.", "success")
            return redirect(url_for('main.historial'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar el registro: {e}", "error")
            print(f"ERROR: Fallo al actualizar en la DB: {e}")

    # Si es GET o la validación falla, renderiza el formulario con los datos existentes
    return render_template("main/edit_registro.html", form=form, registro_id=registro.id, current_year=date.today().year)

# Nueva ruta para el perfil de usuario
@main_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    # Pasa los datos originales del usuario al formulario para la validación de unicidad
    form = UpdateAccountForm(original_username=current_user.username, original_email=current_user.email)

    if form.validate_on_submit():
        # Lógica para actualizar el usuario
        if form.username.data != current_user.username:
            current_user.username = form.username.data
        if form.email.data != current_user.email:
            current_user.email = form.email.data
        
        try:
            db.session.commit()
            flash('Tu cuenta ha sido actualizada con éxito.', 'success')
            return redirect(url_for('main.perfil'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la cuenta: {e}', 'error')
            print(f"ERROR: Fallo al actualizar cuenta en DB: {e}")
    elif request.method == 'GET':
        # Pre-llenar el formulario con la información actual del usuario
        form.username.data = current_user.username
        form.email.data = current_user.email
    
    return render_template('main/perfil.html', title='Perfil de Usuario', form=form, current_year=date.today().year)

# Nueva ruta para el panel de administración
@main_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Verificar si el usuario actual es un administrador o moderador
    if not current_user.is_admin and not current_user.is_moderator:
        flash("No tienes permiso para acceder a esta página.", "error")
        abort(403) # Prohibido

    users = User.query.all() # Obtener todos los usuarios
    users_data = []

    for user in users:
        # Calcular el total de horas para cada usuario
        total_horas_user = sum(registro.horas for registro in user.registros)
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'is_moderator': user.is_moderator, # Incluir el estado de moderador
            'is_owner': user.is_owner, # Include is_owner status
            'total_horas': total_horas_user
        })
    
    return render_template('admin/dashboard.html', users=users_data, current_year=date.today().year)

# Nueva ruta para editar un usuario desde el panel de administración
@main_bp.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    # Solo administradores (o dueños) pueden editar usuarios
    if not current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para editar usuarios.", "error")
        abort(403)

    user_to_edit = User.query.get_or_404(user_id)

    # Un administrador no puede editar a un dueño, a menos que sea el dueño mismo
    if user_to_edit.is_owner and current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para editar la cuenta de un usuario Owner.", "error")
        return redirect(url_for('main.admin_dashboard'))

    # Pasa los datos originales del usuario al formulario para la validación de unicidad
    form = UpdateAccountForm(original_username=user_to_edit.username, original_email=user_to_edit.email)

    if form.validate_on_submit():
        user_to_edit.username = form.username.data
        user_to_edit.email = form.email.data
        try:
            db.session.commit()
            flash(f'Usuario {user_to_edit.username} actualizado con éxito.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el usuario: {e}', 'error')
            print(f"ERROR: Fallo al actualizar usuario en DB: {e}")
    elif request.method == 'GET':
        form.username.data = user_to_edit.username
        form.email.data = user_to_edit.email
    
    return render_template('admin/edit_user.html', form=form, user=user_to_edit, current_year=date.today().year)

# Nueva ruta para restablecer la contraseña de un usuario desde el panel de administración
@main_bp.route('/admin/reset_user_password/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_reset_user_password(user_id):
    # Solo administradores (o dueños) pueden restablecer contraseñas
    if not current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para restablecer contraseñas.", "error")
        abort(403)

    user_to_reset = User.query.get_or_404(user_id)

    # Un administrador no puede restablecer la contraseña de un dueño, a menos que sea el dueño mismo
    if user_to_reset.is_owner and current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para restablecer la contraseña de un usuario Owner.", "error")
        return redirect(url_for('main.admin_dashboard'))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user_to_reset.set_password(form.new_password.data)
        try:
            db.session.commit()
            flash(f'Contraseña de {user_to_reset.username} restablecida con éxito.', 'success')
            return redirect(url_for('main.admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al restablecer la contraseña: {e}', 'error')
            print(f"ERROR: Fallo al restablecer contraseña en DB: {e}")
    
    return render_template('admin/reset_user_password.html', form=form, user=user_to_reset, current_year=date.today().year)

# Nueva ruta para alternar el estado de administrador de un usuario
@main_bp.route('/admin/toggle_admin_status/<int:user_id>', methods=['POST'])
@login_required
def admin_toggle_admin_status(user_id):
    # Solo el dueño puede cambiar el estado de administrador
    if not current_user.is_owner:
        flash("No tienes permiso para cambiar el estado de administrador. Solo el dueño de la aplicación puede hacerlo.", "error")
        abort(403)

    user_to_toggle = User.query.get_or_404(user_id)

    # No permitir que un administrador se quite a sí mismo el rol de administrador
    if user_to_toggle.id == current_user.id:
        flash("No puedes cambiar tu propio estado de administrador desde aquí.", "error")
        return redirect(url_for('main.admin_dashboard'))

    user_to_toggle.is_admin = not user_to_toggle.is_admin
    # Si se convierte en admin, también debe ser moderador (o viceversa si se quita admin y era solo moderador)
    if user_to_toggle.is_admin:
        user_to_toggle.is_moderator = True
    else: # Si se quita el admin, también se quita el moderador
        user_to_toggle.is_moderator = False

    try:
        db.session.commit()
        flash(f'El estado de administrador de {user_to_toggle.username} ha sido cambiado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado de administrador: {e}', "error")
        print(f"ERROR: Fallo al cambiar estado admin en DB: {e}")
    
    return redirect(url_for('main.admin_dashboard'))

# NUEVA RUTA: Alternar el estado de moderador de un usuario
@main_bp.route('/admin/toggle_moderator_status/<int:user_id>', methods=['POST'])
@login_required
def admin_toggle_moderator_status(user_id):
    # Solo administradores (o dueños) pueden cambiar el estado de moderador
    if not current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para cambiar el estado de moderador. Solo un administrador o el dueño de la aplicación pueden hacerlo.", "error")
        abort(403)

    user_to_toggle = User.query.get_or_404(user_id)

    # No permitir que un administrador cambie su propio estado de moderador
    if user_to_toggle.id == current_user.id:
        flash("No puedes cambiar tu propio estado de moderador desde aquí.", "error")
        return redirect(url_for('main.admin_dashboard'))
    
    # Un administrador no puede quitar el rol de moderador a un dueño
    if user_to_toggle.is_owner and current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para cambiar el estado de moderador de un usuario Owner.", "error")
        return redirect(url_for('main.admin_dashboard'))

    # Un administrador no puede cambiar el estado de moderador de otro administrador
    if user_to_toggle.is_admin and not user_to_toggle.is_owner and current_user.is_admin and not current_user.is_owner:
        flash("Un administrador no puede cambiar el estado de moderador de otro administrador.", "error")
        return redirect(url_for('main.admin_dashboard'))

    user_to_toggle.is_moderator = not user_to_toggle.is_moderator
    
    # Si el usuario es admin, siempre debe ser moderador
    if user_to_toggle.is_admin:
        user_to_toggle.is_moderator = True

    try:
        db.session.commit()
        flash(f'El estado de moderador de {user_to_toggle.username} ha sido cambiado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado de moderador: {e}', "error")
        print(f"ERROR: Fallo al cambiar estado moderador en DB: {e}")
    
    return redirect(url_for('main.admin_dashboard'))

# NUEVA RUTA: Eliminar un usuario (y sus registros asociados)
@main_bp.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    # Solo el dueño puede eliminar usuarios
    if not current_user.is_owner:
        flash("No tienes permiso para eliminar usuarios. Solo el dueño de la aplicación puede hacerlo.", "error")
        abort(403)

    user_to_delete = User.query.get_or_404(user_id)

    # No permitir que un usuario se elimine a sí mismo
    if user_to_delete.id == current_user.id:
        flash("No puedes eliminar tu propia cuenta desde aquí.", "error")
        return redirect(url_for('main.admin_dashboard'))
    
    # No permitir que un administrador elimine a un dueño
    if user_to_delete.is_owner and current_user.is_admin and not current_user.is_owner:
        flash("No tienes permiso para eliminar la cuenta de un usuario Owner.", "error")
        return redirect(url_for('main.admin_dashboard'))

    try:
        # Eliminar todos los registros de horas asociados a este usuario primero
        Registro.query.filter_by(user_id=user_to_delete.id).delete()
        Recibo.query.filter_by(user_id=user_to_delete.id).delete() # Eliminar recibos asociados
        
        # Ahora elimina el usuario
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuario {user_to_delete.username} y sus registros han sido eliminados con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {e}', "error")
        print(f"ERROR: Fallo al eliminar usuario en DB: {e}")
    
    return redirect(url_for('main.admin_dashboard'))


# Ruta para eliminar un registro (del historial propio del usuario)
@main_bp.route('/eliminar_registro/<int:registro_id>', methods=['POST'])
@login_required
def delete_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)

    if registro.user_id != current_user.id:
        flash("No tienes permiso para eliminar este registro.", "error")
        abort(403)

    try:
        db.session.delete(registro)
        db.session.commit()
        flash("Registro eliminado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el registro: {e}", "error")
        print(f"ERROR: Fallo al eliminar en la DB: {e}")
    
    return redirect(url_for('main.historial'))

# --- Rutas para Recibos de Sueldo ---
# Nueva ruta para la verificación antes de acceder a los recibos
@main_bp.route('/recibos/verificar', methods=['GET', 'POST'])
@login_required
def verificar_recibos():
    form = VerifyRecibosForm()
    if form.validate_on_submit():
        if form.legajo.data == current_user.username and current_user.check_password(form.password.data):
            session['recibos_verified'] = True
            session.permanent = True
            current_app.permanent_session_lifetime = timedelta(minutes=10)
            flash('Acceso verificado. Redirigiendo a tus recibos.', 'success')
            return redirect(url_for('main.recibos'))
        else:
            flash('Legajo o contraseña incorrectos.', 'error')
    return render_template('main/recibos_verificar.html', form=form, current_year=date.today().year)


@main_bp.route('/recibos', methods=['GET', 'POST'])
@login_required
def recibos():
    if not session.get('recibos_verified'):
        flash('Por favor, verifica tu acceso para ver los recibos de sueldo.', 'info')
        return redirect(url_for('main.verificar_recibos'))

    os.makedirs(os.path.join(current_app.root_path, UPLOAD_FOLDER), exist_ok=True)

    if request.method == 'POST':
        if 'recibo_file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(request.url)
        
        file = request.files['recibo_file']

        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, filename)
            
            try:
                file.save(file_path)
                
                new_recibo = Recibo(
                    filename=filename,
                    upload_date=datetime.utcnow(),
                    user_id=current_user.id
                )
                db.session.add(new_recibo)
                db.session.commit()
                flash('Recibo subido con éxito.', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al subir el recibo: {e}', 'error')
                print(f"ERROR: Fallo al subir recibo: {e}")
            return redirect(url_for('main.recibos'))
        else:
            flash('Tipo de archivo no permitido. Solo PDF, PNG, JPG, JPEG son aceptados.', 'error')
            return redirect(request.url)

    user_recibos = Recibo.query.filter_by(user_id=current_user.id).order_by(Recibo.upload_date.desc()).all()
    return render_template('main/recibos.html', recibos=user_recibos, current_year=date.today().year)

@main_bp.route('/recibos/view/<int:recibo_id>')
@login_required
def view_recibo(recibo_id):
    if not session.get('recibos_verified'):
        flash('Por favor, verifica tu acceso para ver los recibos de sueldo.', 'info')
        return redirect(url_for('main.verificar_recibos'))

    recibo = Recibo.query.get_or_404(recibo_id)

    if recibo.user_id != current_user.id:
        flash("No tienes permiso para ver este recibo.", "error")
        abort(403)

    file_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, recibo.filename)
    
    if not os.path.exists(file_path):
        flash("El archivo del recibo no se encontró en el servidor.", "error")
        abort(404)

    mimetype = 'application/pdf'
    if recibo.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        mimetype = f'image/{recibo.filename.rsplit(".", 1)[1].lower()}'

    return send_file(file_path, mimetype=mimetype)

@main_bp.route('/recibos/delete/<int:recibo_id>', methods=['POST'])
@login_required
def delete_recibo(recibo_id):
    if not session.get('recibos_verified'):
        flash('Por favor, verifica tu acceso para eliminar recibos de sueldo.', 'info')
        return redirect(url_for('main.verificar_recibos'))

    recibo = Recibo.query.get_or_404(recibo_id)

    if recibo.user_id != current_user.id:
        flash("No tienes permiso para eliminar este recibo.", "error")
        abort(403)

    file_path = os.path.join(current_app.root_path, UPLOAD_FOLDER, recibo.filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        
        db.session.delete(recibo)
        db.session.commit()
        flash('Recibo eliminado con éxito.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el recibo: {e}', 'error')
        print(f"ERROR: Fallo al eliminar recibo: {e}")
    
    return redirect(url_for('main.recibos'))

# Nueva ruta para redirigir a la web externa de recibos
@main_bp.route('/recibos/ir_web_externa')
@login_required
def go_to_external_recibos():
    # Asegúrate de que el usuario ha pasado la verificación para recibos
    if not session.get('recibos_verified'):
        flash('Por favor, verifica tu acceso para ir a la plataforma externa de recibos.', 'info')
        return redirect(url_for('main.verificar_recibos'))

    external_url = os.getenv('RECIBOS_SUELDO')
    if external_url:
        flash('Redirigiendo a la plataforma externa de recibos. Es posible que debas iniciar sesión nuevamente allí.', 'info')
        return redirect(external_url)
    else:
        flash('La URL de la plataforma externa de recibos no está configurada. Contacta al administrador.', 'error')
        return redirect(url_for('main.recibos'))
