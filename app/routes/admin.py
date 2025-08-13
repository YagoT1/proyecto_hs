from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, abort
from flask_login import login_required, current_user
from app.models import User
from app import db, bcrypt # Asegúrate de importar bcrypt aquí si lo usas para set_password directamente
from sqlalchemy import case, asc
from app.utils import obtener_rol
from datetime import datetime, timedelta

admin = Blueprint('admin', __name__)

# Restricción de acceso solo a administradores o propietarios
@admin.before_request
@login_required
def admin_required():
    if not current_user.is_admin and not current_user.is_owner:
        flash('No tienes permiso para acceder a esta página.', 'danger')
        abort(403) # Usar abort(403) para Forbidden

@admin.route('/admin_dashboard')
def admin_dashboard():
    """
    Ruta para el panel de administración.
    Muestra una lista de todos los usuarios registrados.
    """
    try:
        users_from_db = User.query.order_by(
            case((User.area == None, 1), else_=0),
            asc(User.area),
            asc(User.username)
        ).all()

        user_data = []
        for user in users_from_db:
            # Calcular si el usuario está online (última actividad en los últimos 5 minutos)
            is_online = False
            if user.last_seen:
                is_online = (datetime.utcnow() - user.last_seen).total_seconds() < 300 # 300 segundos = 5 minutos

            user_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'area': user.area or 'Sin asignar',
                'rol': obtener_rol(user), # Usa la función obtener_rol
                'is_admin': user.is_admin, # Necesario para los botones de toggle
                'is_moderator': user.is_moderator, # Necesario para los botones de toggle
                'is_owner': user.is_owner, # Necesario para los botones de toggle
                'ultimo_acceso': user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else "Nunca",
                'is_online': is_online # ¡NUEVO CAMPO!
            })

        return render_template('admin/dashboard.html', title='Panel de Administración', users=user_data)

    except Exception as e:
        current_app.logger.error(f'Error al cargar el panel de administración: {str(e)}')
        flash('Ocurrió un error al cargar los usuarios.', 'danger')
        return redirect(url_for('main.index')) # Redirigir a una ruta segura si hay un error grave


# --- Toggle Admin ---
@admin.route('/user/<int:user_id>/toggle_admin')
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)

    # No permitir que un admin cambie su propio rol de admin
    if user.id == current_user.id:
        flash('No puedes modificar tu propio rol de administrador.', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    # No permitir que un admin cambie el rol de un owner
    if user.is_owner and not current_user.is_owner:
        flash('No tienes permiso para modificar el rol de un propietario.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f'Rol de administrador {"asignado" if user.is_admin else "revocado"} correctamente para {user.username}.', 'success')
    return redirect(url_for('admin.admin_dashboard'))


# --- Toggle Moderator ---
@admin.route('/user/<int:user_id>/toggle_moderator')
def toggle_moderator(user_id):
    user = User.query.get_or_404(user_id)

    # No permitir que un admin cambie el rol de un owner
    if user.is_owner and not current_user.is_owner:
        flash('No tienes permiso para modificar el rol de un propietario.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    user.is_moderator = not user.is_moderator
    db.session.commit()
    flash(f'Rol de moderador {"asignado" if user.is_moderator else "revocado"} correctamente para {user.username}.', 'success')
    return redirect(url_for('admin.admin_dashboard'))


# --- Eliminar usuario ---
@admin.route('/user/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    # No permitir que un admin elimine su propio usuario
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario.', 'warning')
        return redirect(url_for('admin.admin_dashboard'))

    # No permitir que un admin elimine a un owner
    if user.is_owner and not current_user.is_owner:
        flash('No tienes permiso para eliminar a un propietario.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Usuario {user.username} eliminado correctamente.', 'success')
    return redirect(url_for('admin.admin_dashboard'))


# --- Editar usuario ---
@admin.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    # No permitir que un admin edite a un owner (excepto si es el owner)
    if user.is_owner and not current_user.is_owner:
        flash('No tienes permiso para editar a un propietario.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.area = request.form.get('area') # Usar .get() para evitar KeyError si no se envía

        # Opcional: Validar que el email no exista ya para otro usuario
        existing_user_with_email = User.query.filter(User.email == user.email, User.id != user.id).first()
        if existing_user_with_email:
            flash('Ese email ya está en uso por otro usuario.', 'danger')
            return render_template('admin/edit_user.html', user=user)

        db.session.commit()
        flash(f'Datos del usuario {user.username} actualizados correctamente.', 'success')
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin/edit_user.html', title=f'Editar Usuario: {user.username}', user=user)


# --- Restablecer contraseña desde el panel de administración ---
@admin.route('/user/<int:user_id>/reset_password_admin', methods=['POST'])
def reset_user_password_admin(user_id):
    user = User.query.get_or_404(user_id)

    # No permitir que un admin restablezca la contraseña de un owner (excepto si es el owner)
    if user.is_owner and not current_user.is_owner:
        flash('No tienes permiso para restablecer la contraseña de un propietario.', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or not confirm_password:
        flash('Ambos campos de contraseña son requeridos.', 'warning')
        return redirect(url_for('admin.edit_user', user_id=user.id))

    if new_password != confirm_password:
        flash('Las contraseñas no coinciden.', 'warning')
        return redirect(url_for('admin.edit_user', user_id=user.id))

    if len(new_password) < 6: # Ejemplo de validación de longitud
        flash('La nueva contraseña debe tener al menos 6 caracteres.', 'warning')
        return redirect(url_for('admin.edit_user', user_id=user.id))

    user.set_password(new_password) # Usa el método set_password del modelo User
    db.session.commit()
    flash(f'Contraseña para {user.username} restablecida correctamente.', 'success')
    return redirect(url_for('admin.admin_dashboard'))
