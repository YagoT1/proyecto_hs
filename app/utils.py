from flask_mail import Message
from flask import url_for, current_app
from app import mail  # Instancia de Flask-Mail
from app.models import User  # Modelo de usuario

def send_reset_email(user):
    """
    Envía un correo de restablecimiento de contraseña al usuario indicado.
    """
    token = user.get_reset_token()
    
    reset_url = url_for('auth.reset_token', token=token, _external=True)

    msg = Message(
        subject='Solicitud de Restablecimiento de Contraseña',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    
    msg.body = (
        f"Hola {user.username},\n\n"
        f"Haz solicitado restablecer tu contraseña. Para continuar, accede al siguiente enlace:\n\n"
        f"{reset_url}\n\n"
        "Este enlace es válido por un tiempo limitado.\n"
        "Si tú no solicitaste este cambio, puedes ignorar este mensaje sin realizar ninguna acción.\n\n"
        "Saludos,\n"
        "El equipo de soporte"
    )

    try:
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Error al enviar correo de restablecimiento: {e}")

def obtener_rol(user):
    """
    Determina y devuelve el rol principal de un usuario.
    La prioridad es: Owner > Admin > Moderator > User.
    """
    if user.is_owner:
        return 'Owner'
    elif user.is_admin:
        return 'Admin'
    elif user.is_moderator:
        return 'Moderador'
    else:
        return 'Usuario'
