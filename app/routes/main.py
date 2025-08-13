import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, make_response, abort, send_from_directory
from flask_login import login_required, current_user
from flask_mail import Message
from app.forms import ErrorReportForm
from datetime import datetime, timedelta
from app.models import Registro, User, Recibo
from app import db
from flask_wtf.csrf import generate_csrf, validate_csrf
from sqlalchemy import func # Importar func para operaciones de base de datos

# Importaciones para ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont # Para fuentes personalizadas si es necesario
import io

main = Blueprint('main', __name__)

# --- Funciones de utilidad para archivos ---
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Rutas principales del dashboard ---

@main.route('/')
@main.route('/index')
@login_required
def index():
    """
    Ruta principal del dashboard.
    Muestra un resumen de horas y la información de la cuenta del usuario.
    """
    last_login_time_local = getattr(current_user, 'last_login', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    registered_at_local = getattr(current_user, 'registered_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    
    today = datetime.now()
    current_year = today.year
    current_month = today.month # Pasar el mes actual

    total_hours_query = db.session.query(db.func.sum(Registro.horas)).filter_by(user_id=current_user.id).scalar()
    total_hours = total_hours_query if total_hours_query is not None else 0.0

    first_day_of_current_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
    first_day_of_previous_month = last_day_of_previous_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    previous_month_hours_query = db.session.query(db.func.sum(Registro.horas)).filter(
        Registro.user_id == current_user.id,
        Registro.fecha >= first_day_of_previous_month.date(),
        Registro.fecha < first_day_of_current_month.date()
    ).scalar()
    previous_month_hours = previous_month_hours_query if previous_month_hours_query is not None else 0.0

    return render_template("index.html",
                           title='Dashboard',
                           total_hours=total_hours,
                           previous_month_hours=previous_month_hours,
                           last_login_time_local=last_login_time_local,
                           registered_at_local=registered_at_local,
                           current_year=current_year,
                           current_month=current_month)
                           
@main.route('/registrar_horas', methods=['GET', 'POST'])
@login_required
def registrar_horas():
    """
    Endpoint para registrar un nuevo usuario.
    Requiere username, email y password.
    """
    if request.method == 'POST':
        received_csrf_token = request.form.get('csrf_token')
        try:
            validate_csrf(received_csrf_token)
        except Exception as e:
            flash('Error de seguridad: Token CSRF inválido. Por favor, inténtalo de nuevo.', 'danger')
            current_app.logger.error(f"ERROR CSRF (POST): Fallo de validación del token: {e}")
            return redirect(url_for('main.registrar_horas'))

        registros_a_guardar = []
        errors = []

        i = 0
        while True:
            fecha_key = f'fecha_{i}'
            horas_key = f'horas_{i}'
            obs_key = f'obs_{i}'
            feriado_key = f'feriado_{i}'

            if fecha_key not in request.form:
                break

            fecha_str = request.form.get(fecha_key)
            horas_str = request.form.get(horas_key)
            observacion = request.form.get(obs_key, '')
            es_feriado = request.form.get(feriado_key) == 'on'

            if not fecha_str:
                errors.append(f"La fecha es requerida para el registro {i+1}.")
            if not horas_str:
                errors.append(f"Las horas son requeridas para el registro {i+1}.")

            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                horas = float(horas_str.replace(',', '.'))

                if not (0.1 <= horas <= 24.0):
                    errors.append(f"Horas inválidas para el registro {i+1}: {horas_str}. Debe ser entre 0.1 y 24.0.")

                registros_a_guardar.append(Registro(
                    fecha=fecha,
                    horas=horas,
                    observacion=observacion,
                    tipo='feriado' if es_feriado else 'normal',
                    user_id=current_user.id
                ))
            except (ValueError, TypeError) as e:
                errors.append(f"Error de formato en el registro {i+1}: {e}. Asegúrate de que la fecha y las horas sean correctas y numéricas.")

            i += 1

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('main/registrar_horas.html', title='Registrar Horas', csrf_token=generate_csrf())

        if not registros_a_guardar:
            flash('No se enviaron registros para guardar.', 'danger')
            return render_template('main/registrar_horas.html', title='Registrar Horas', csrf_token=generate_csrf())

        try:
            db.session.add_all(registros_a_guardar)
            db.session.commit()
            flash(f'¡{len(registros_a_guardar)} registro(s) de horas guardado(s) exitosamente!', 'success')
            return redirect(url_for('main.ver_historial'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar los registros en la base de datos: {e}', 'danger')
            current_app.logger.error(f"ERROR (POST): Fallo al guardar los registros: {e}")

    generated_csrf = generate_csrf()
    return render_template('main/registrar_horas.html', title='Registrar Horas', csrf_token=generated_csrf)

@main.route('/historial')
@login_required
def ver_historial():
    """
    Muestra la página con el selector para elegir un mes y año.
    """
    # Obtener la lista de meses disponibles para el selector
    available_months_data = []
    try:
        available_months_query = db.session.query(
            func.extract('year', Registro.fecha).label('year'),
            func.extract('month', Registro.fecha).label('month')
        ).filter(Registro.user_id == current_user.id)\
         .group_by('year', 'month')\
         .order_by('year', 'month').all()
        
        for ym in available_months_query:
            date_obj = datetime(int(ym.year), int(ym.month), 1)
            available_months_data.append({
                'year': int(ym.year),
                'month': int(ym.month),
                'display_name': date_obj.strftime('%B %Y').capitalize()
            })
        current_app.logger.debug(f"ver_historial: Meses disponibles para selector (desde DB): {available_months_data}")
    except Exception as e:
        current_app.logger.error(f"ver_historial: ERROR al obtener meses disponibles desde DB: {e}")
        flash('Ocurrió un error al cargar la lista de meses disponibles.', 'danger')
        available_months_data = [] # Asegurarse de que esté vacío si falla

    # Establecer el mes y año por defecto para la selección inicial (mes actual)
    today = datetime.now()
    selected_year = today.year
    selected_month = today.month

    return render_template('main/ver_historial.html', 
                           title='Seleccionar Historial de Horas', 
                           csrf_token=generate_csrf(),
                           selected_year=selected_year,
                           selected_month=selected_month,
                           available_months=available_months_data)

@main.route('/historial/mostrar/<int:year>/<int:month>', methods=['GET'])
@login_required
def mostrar_historial_detallado(year, month):
    """
    Muestra el historial de registros de horas del usuario actual para un mes y año específicos.
    Esta es la página de destino después de seleccionar un mes.
    """
    try:
        target_date = datetime(year, month, 1)
    except ValueError:
        flash('Fecha inválida. Volviendo al selector de historial.', 'warning')
        return redirect(url_for('main.ver_historial'))

    month_name = target_date.strftime('%B').capitalize()
    year_display = target_date.year

    registros = Registro.query.filter(
        Registro.user_id == current_user.id,
        func.extract('year', Registro.fecha) == year_display,
        func.extract('month', Registro.fecha) == target_date.month
    ).order_by(Registro.fecha.desc(), Registro.timestamp.desc()).all()

    current_app.logger.debug(f"mostrar_historial_detallado: Consulta para {current_user.username} en {month_name} {year_display}. Registros encontrados: {len(registros)}")
    
    return render_template('main/historial_detallado.html', 
                           title=f'Historial de Horas - {month_name} {year_display}', 
                           registros=registros, 
                           csrf_token=generate_csrf(),
                           current_month_name=month_name,
                           current_year=year_display,
                           selected_year=year_display, # Mantener la selección para el PDF
                           selected_month=target_date.month) # Mantener la selección para el PDF


@main.route('/registro/<int:registro_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_registro(registro_id):
    """
    Permite editar un registro de horas existente.
    """
    registro = Registro.query.get_or_404(registro_id)

    if registro.user_id != current_user.id:
        flash('No tienes permiso para editar este registro.', 'danger')
        abort(403)

    if request.method == 'GET':
        return render_template('main/editar_registro.html',
                               title='Editar Registro',
                               registro=registro,
                               csrf_token=generate_csrf())
    
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
            fecha_str = request.form.get('fecha')
            horas_str = request.form.get('horas')
            observacion = request.form.get('observacion', '')

            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            horas = float(horas_str.replace(',', '.'))

            registro.fecha = fecha
            registro.horas = horas
            registro.observacion = observacion
            db.session.commit()
            flash('Registro de horas actualizado exitosamente!', 'success')
            # Redirigir al historial detallado del mes del registro editado
            return redirect(url_for('main.mostrar_historial_detallado', 
                                     year=registro.fecha.year, 
                                     month=registro.fecha.month))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el registro: {e}', 'danger')
            current_app.logger.error(f"ERROR: Fallo al actualizar el registro: {e}")
            return render_template('main/editar_registro.html',
                                   title='Editar Registro',
                                   registro=registro,
                                   csrf_token=generate_csrf())

@main.route('/registro/<int:registro_id>/eliminar', methods=['POST'])
@login_required
def eliminar_registro(registro_id):
    """
    Permite eliminar un registro de horas.
    """
    registro = Registro.query.get_or_404(registro_id)

    if registro.user_id != current_user.id:
        flash('No tienes permiso para eliminar este registro.', 'danger')
        abort(403)

    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash('Error de seguridad: Token CSRF inválido. Por favor, inténtalo de nuevo.', 'danger')
        current_app.logger.error(f"ERROR CSRF: {e}")
        return redirect(url_for('main.ver_historial'))

    try:
        db.session.delete(registro)
        db.session.commit()
        flash('Registro de horas eliminado exitosamente!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el registro: {e}', 'danger')
        current_app.logger.error(f"Error al eliminar el registro: {e}")
    
    return redirect(url_for('main.ver_historial'))

@main.route('/generate_historial_pdf/<int:year>/<int:month>')
@login_required
def generate_historial_pdf_by_month(year, month):
    """
    Genera un PDF con el historial de horas del usuario actual para un mes y año específicos.
    """
    try:
        target_date = datetime(year, month, 1)
    except ValueError:
        flash('Fecha inválida para generar PDF.', 'danger')
        return redirect(url_for('main.ver_historial'))

    month_name = target_date.strftime('%B').capitalize()
    year_display = target_date.year

    historial_horas = Registro.query.filter(
        Registro.user_id == current_user.id,
        func.extract('year', Registro.fecha) == year_display,
        func.extract('month', Registro.fecha) == target_date.month
    ).order_by(Registro.fecha.asc()).all()

    buffer = io.BytesIO()
    
    # Configurar el documento con márgenes adecuados para impresión
    doc = SimpleDocTemplate(buffer, 
                            pagesize=letter,
                            leftMargin=0.75 * inch,
                            rightMargin=0.75 * inch,
                            topMargin=0.75 * inch,
                            bottomMargin=0.75 * inch)
    
    styles = getSampleStyleSheet()
    
    # Definir un estilo para el título del documento
    styles.add(ParagraphStyle(name='CustomTitle',
                              parent=styles['h1'],
                              fontSize=18,
                              leading=22,
                              alignment=1, # Center alignment
                              spaceAfter=14, # Space after title
                              textColor=colors.black)) # Color de texto negro para el título

    # Definir un estilo para el texto normal en la tabla
    styles.add(ParagraphStyle(name='TableCellText',
                              parent=styles['Normal'],
                              fontSize=10,
                              leading=12,
                              textColor=colors.black)) # Color de texto negro para las celdas

    story = []

    # Título del PDF
    story.append(Paragraph(f"Historial de Horas - {month_name} {year_display} - {current_user.username}", styles['CustomTitle']))
    story.append(Spacer(1, 0.2 * inch))

    if not historial_horas:
        story.append(Paragraph(f"No hay registros de horas para generar el PDF para {month_name} {year_display}.", styles['TableCellText']))
    else:
        # Preparar datos para la tabla
        # Encabezados de la tabla
        data = [[
            Paragraph("Fecha", styles['TableCellText']),
            Paragraph("Horas", styles['TableCellText']),
            Paragraph("Observación", styles['TableCellText']),
            Paragraph("Tipo", styles['TableCellText'])
        ]]
        
        for registro in historial_horas:
            # Usar el estilo TableCellText para el contenido de la tabla
            observacion_paragraph = Paragraph(registro.observacion or '', styles['TableCellText'])
            tipo_paragraph = Paragraph(registro.tipo.capitalize() if registro.tipo else 'Normal', styles['TableCellText'])
            
            data.append([
                Paragraph(registro.fecha.strftime('%Y-%m-%d'), styles['TableCellText']),
                Paragraph(f"{registro.horas:.2f}", styles['TableCellText']),
                observacion_paragraph,
                tipo_paragraph
            ])

        # Estilo de la tabla
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Encabezado: gris claro
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black), # Texto del encabezado: negro
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white), # Filas de datos: blanco
            ('GRID', (0, 0), (-1, -1), 1, colors.grey), # Cuadrícula: gris
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black), # Texto de las celdas: negro
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0,0), (-1,-1), 'TOP'), # Alineación vertical superior para todas las celdas
        ])

        # Anchos de columna ajustados para un mejor ajuste en la página
        # Asegurarse de que la suma de los anchos no exceda el ancho de la página - márgenes
        # Ancho total disponible = 8.5 inch (letter width) - 0.75*2 inch (margins) = 7 inch
        col_widths = [1.0*inch, 0.7*inch, 4.5*inch, 0.8*inch] # Ajustado el ancho de Observación
        table = Table(data, colWidths=col_widths)
        table.setStyle(table_style)
        story.append(table)

    doc.build(story)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=historial_horas_{current_user.username}_{month_name}_{year_display}.pdf'
    return response


@main.route('/mis_recibos', methods=['GET', 'POST'])
@login_required
def mis_recibos():
    """
    Ruta para ver y subir recibos del usuario.
    """
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
        except Exception as e:
            flash('Error de seguridad: Token CSRF inválido. Por favor, inténtalo de nuevo.', 'danger')
            current_app.logger.error(f"CSRF Error al subir recibo: {e}")
            return redirect(url_for('main.mis_recibos'))

        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(request.url)
        file = request.files['file']

        if file.filename == '':
            flash('No se seleccionó ningún archivo.', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            
            try:
                os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(filepath)

                new_recibo = Recibo(
                    filename=filename,
                    filepath=filepath,
                    user_id=current_user.id
                )
                db.session.add(new_recibo)
                db.session.commit()
                flash('Recibo subido exitosamente!', 'success')
            except Exception as e:
                db.session.rollback()
                flash(f'Error al subir el recibo: {e}', 'danger')
                current_app.logger.error(f"Error al guardar recibo en DB o disco: {e}")
        else:
            flash('Tipo de archivo no permitido. Solo se permiten PDF, JPG, JPEG, PNG.', 'danger')
        
        return redirect(url_for('main.mis_recibos'))

    recibos = Recibo.query.filter_by(user_id=current_user.id).order_by(Recibo.upload_date.desc()).all()
    return render_template('main/mis_recibos.html', 
                           title='Mis Recibos', 
                           recibos=recibos, 
                           csrf_token=generate_csrf())

@main.route('/download_recibo/<int:recibo_id>')
@login_required
def download_recibo(recibo_id):
    """
    Permite al usuario descargar uno de sus recibos.
    """
    recibo = Recibo.query.get_or_404(recibo_id)
    if recibo.user_id != current_user.id:
        flash('No tienes permiso para descargar este recibo.', 'danger')
        abort(403)
    
    try:
        directory = os.path.dirname(recibo.filepath)
        filename = os.path.basename(recibo.filepath)
        return send_from_directory(directory, filename, as_attachment=True, download_name=recibo.filename)
    except Exception as e:
        flash(f'Error al descargar el recibo: {e}', 'danger')
        current_app.logger.error(f"Error al descargar recibo {recibo_id}: {e}")
        return redirect(url_for('main.mis_recibos'))

@main.route('/delete_recibo/<int:recibo_id>', methods=['POST'])
@login_required
def delete_recibo(recibo_id):
    """
    Permite al usuario eliminar uno de sus recibos.
    """
    recibo = Recibo.query.get_or_404(recibo_id)
    if recibo.user_id != current_user.id:
        flash('No tienes permiso para eliminar este recibo.', 'danger')
        abort(403)
    
    try:
        validate_csrf(request.form.get('csrf_token'))
    except Exception as e:
        flash('Error de seguridad: Token CSRF inválido. Por favor, inténtalo de nuevo.', 'danger')
        current_app.logger.error(f"CSRF Error al eliminar recibo: {e}")
        return redirect(url_for('main.mis_recibos'))

    try:
        if os.path.exists(recibo.filepath):
            os.remove(recibo.filepath)
        
        db.session.delete(recibo)
        db.session.commit()
        flash('Recibo eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el recibo: {e}', 'danger')
        current_app.logger.error(f"Error al eliminar recibo {recibo_id} del disco o DB: {e}")
    
    return redirect(url_for('main.mis_recibos'))

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Ruta para el perfil del usuario, permite editar el área.
    """
    if request.method == 'POST':
        try:
            validate_csrf(request.form.get('csrf_token'))
            new_area = request.form.get('area')
            
            if new_area is not None:
                current_user.area = new_area
                db.session.commit()
                flash('Tu área ha sido actualizada exitosamente.', 'success')
            else:
                flash('No se recibió el campo de área.', 'danger')
            
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocurrió un error al actualizar tu área: {e}', 'danger')
            current_app.logger.error(f"Error al actualizar área del usuario {current_user.username}: {e}")

    last_login_time_local = getattr(current_user, 'last_login', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')
    registered_at_local = getattr(current_user, 'registered_at', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')

    return render_template('main/perfil.html', 
                           title='Mi Perfil', 
                           user=current_user,
                           last_login_time_local=last_login_time_local,
                           registered_at_local=registered_at_local,
                           csrf_token=generate_csrf())

# --- Ruta para el reporte de errores ---

@main.route('/report_error', methods=['GET', 'POST'])
def report_error():
    """
    Ruta para que los usuarios reporten errores.
    """
    form = ErrorReportForm()
    if form.validate_on_submit():
        mail_instance = current_app.extensions['mail']

        msg = Message(
            f"Reporte de Error: {form.subject.data}",
            sender=current_app.config['MAIL_USERNAME'],
            recipients=current_app.config['ADMINS']
        )
        msg.body = f"""
        Reporte de Error de la aplicación:

        Email del usuario (opcional): {form.email.data or 'No proporcionado'}
        Asunto: {form.subject.data}
        Mensaje:
        {form.message.data}

        URL desde donde se reportó: {request.referrer or 'Desconocida'}
        Usuario (si logueado): {current_user.username if current_user.is_authenticated else 'Anónimo'}
        """
        try:
            mail_instance.send(msg)
            flash('¡Gracias! Tu reporte de error ha sido enviado.', 'success')
        except Exception as e:
            flash(f'Hubo un problema al enviar el reporte de error: {e}', 'danger')
            current_app.logger.error(f"Error al enviar reporte de error: {e}")

        return redirect(url_for('main.index'))

    return render_template('error_report_page.html', title='Reportar Error', form=form)


# --- Manejadores de errores ---

@main.app_errorhandler(400)
def bad_request_error(error):
    """
    Manejador para errores 400 (Bad Request).
    Renderiza la plantilla 400.html.
    """
    form = ErrorReportForm()
    return render_template('errors/400.html', form=form), 400

@main.app_errorhandler(401)
def unauthorized_error(error):
    """
    Manejador para errores 401 (Unauthorized).
    Renderiza la plantilla 401.html.
    """
    form = ErrorReportForm()
    return render_template('errors/401.html', form=form), 401

@main.app_errorhandler(403)
def forbidden_error(error):
    """
    Manejador para errores 403 (Forbidden).
    Renderiza la plantilla 403.html.
    """
    form = ErrorReportForm()
    return render_template('errors/403.html', form=form), 403

@main.app_errorhandler(404)
def not_found_error(error):
    """
    Manejador para errores 404 (Not Found).
    Renderiza la plantilla 404.html.
    """
    form = ErrorReportForm()
    return render_template('errors/404.html', form=form), 404

@main.app_errorhandler(500)
def internal_error(error):
    """
    Manejador para errores 500 (Internal Server Error).
    Renderiza la plantilla 500.html.
    """
    form = ErrorReportForm()
    return render_template('errors/500.html', form=form), 500

@main.app_errorhandler(502)
def bad_gateway_error(error):
    """
    Manejador para errores 502 (Bad Gateway).
    Renderiza la plantilla 502.html.
    """
    form = ErrorReportForm()
    return render_template('errors/502.html', form=form), 502
