# proyecto_hs/app/routes/main.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db # Importa 'db' desde el paquete 'app'
from app.models import Registro # Importa el modelo Registro
from app.forms import RegistroForm # Importa el formulario RegistroForm
from datetime import datetime
from sqlalchemy import extract # Para extraer año/mes de fechas en consultas

# Define el Blueprint para las rutas principales de la aplicación
# No tiene 'url_prefix' porque son las rutas de nivel superior (ej. /dashboard, /historial)
main = Blueprint('main', __name__)

@main.route('/')
@main.route('/dashboard')
@login_required # Esta ruta requiere que el usuario esté autenticado
def dashboard():
    # Puedes crear una instancia del formulario para usarlo directamente en el dashboard
    form = RegistroForm()
    # Opcional: Obtener los últimos 5 registros del usuario para mostrar en el dashboard
    recent_registros = Registro.query.filter_by(user_id=current_user.id).order_by(Registro.timestamp.desc()).limit(5).all()
    return render_template('index.html', title='Dashboard', form=form, recent_registros=recent_registros)

@main.route('/registrar_horas', methods=['GET', 'POST'])
@login_required
def registrar_horas():
    form = RegistroForm()
    if form.validate_on_submit():
        # Validar para evitar registros duplicados para la misma fecha y usuario
        existing_registro = Registro.query.filter_by(
            user_id=current_user.id,
            fecha=form.fecha.data
        ).first()

        if existing_registro:
            flash(f'Ya existe un registro para la fecha {form.fecha.data.strftime("%d-%m-%Y")} para este usuario.', 'danger')
        else:
            registro = Registro(
                user_id=current_user.id,
                fecha=form.fecha.data,
                horas=form.horas.data,
                tipo=form.tipo.data,
                observacion=form.observacion.data
            )
            db.session.add(registro)
            db.session.commit()
            flash('¡Horas extra registradas con éxito!', 'success')
            return redirect(url_for('main.dashboard')) # Redirige al dashboard
    # Renderiza la plantilla del formulario si es un GET o si la validación falla
    return render_template('main/registrar_horas.html', title='Registrar Horas', form=form)

@main.route('/historial')
@login_required
def historial():
    # Obtener año y mes de los parámetros de la URL, o usar el actual por defecto
    year = request.args.get('year', type=int, default=datetime.now().year)
    month = request.args.get('month', type=int, default=datetime.now().month)

    # Consulta los registros del usuario actual para el año y mes seleccionados
    registros = Registro.query.filter_by(user_id=current_user.id) \
                             .filter(extract('year', Registro.fecha) == year) \
                             .filter(extract('month', Registro.fecha) == month) \
                             .order_by(Registro.fecha.asc()) \
                             .all()

    # Obtener todos los pares (año, mes) únicos de los registros del usuario para el filtro de fechas
    available_dates = db.session.query(
        extract('year', Registro.fecha),
        extract('month', Registro.fecha)
    ).filter_by(user_id=current_user.id).distinct().order_by(1, 2).all() # Ordena por año, luego por mes

    return render_template('historial.html',
                           title='Historial',
                           registros=registros,
                           year=year,
                           month=month,
                           available_dates=available_dates)

@main.route('/editar_registro/<int:registro_id>', methods=['GET', 'POST'])
@login_required
def editar_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id) # Obtiene el registro o un 404
    # Seguridad: Asegúrate de que el usuario actual es el dueño del registro
    if registro.user_id != current_user.id:
        flash('No tienes permiso para editar este registro.', 'danger')
        return redirect(url_for('main.historial'))

    form = RegistroForm(obj=registro) # Popula el formulario con los datos existentes del registro
    if form.validate_on_submit():
        # Validar que la fecha editada no cree un duplicado con otro registro existente (excluyendo el actual)
        existing_registro_for_date = Registro.query.filter_by(
            user_id=current_user.id,
            fecha=form.fecha.data
        ).filter(Registro.id != registro_id).first()

        if existing_registro_for_date:
            flash(f'Ya existe otro registro para la fecha {form.fecha.data.strftime("%d-%m-%Y")} para este usuario.', 'danger')
        else:
            registro.fecha = form.fecha.data
            registro.horas = form.horas.data
            registro.tipo = form.tipo.data
            registro.observacion = form.observacion.data
            db.session.commit()
            flash('Registro actualizado con éxito.', 'success')
            return redirect(url_for('main.historial'))
    return render_template('main/editar_registro.html', title='Editar Registro', form=form, registro=registro)

@main.route('/eliminar_registro/<int:registro_id>', methods=['POST'])
@login_required
def eliminar_registro(registro_id):
    registro = Registro.query.get_or_404(registro_id)
    # Seguridad: Asegúrate de que el usuario actual es el dueño del registro
    if registro.user_id != current_user.id:
        flash('No tienes permiso para eliminar este registro.', 'danger')
        return redirect(url_for('main.historial'))

    db.session.delete(registro) # Elimina el registro
    db.session.commit()
    flash('Registro eliminado con éxito.', 'success')
    return redirect(url_for('main.historial'))