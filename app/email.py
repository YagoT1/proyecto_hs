from flask_mail import Message
from flask import url_for, current_app
from app import mail
from threading import Thread

def send_async_email(app, msg):
    """
    Envía un email de forma asíncrona para no bloquear la ejecución.
    """
    with app.app_context():
        mail.send(msg)

def send_reset_email(user):
    """
    Envía un correo para restablecimiento de contraseña con token seguro.
    """
    token = user.get_reset_token()
    app = current_app._get_current_object()
    msg = Message('Restablece tu contraseña',
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    reset_url = url_for('auth.reset_token', token=token, _external=True)
    msg.body = f'''Hola {user.username},

Has solicitado restablecer tu contraseña. Por favor, haz clic en el siguiente enlace para completar el proceso:

{reset_url}

Si no solicitaste este cambio, simplemente ignora este correo.

Saludos cordiales,
El equipo de soporte.
'''
    # Enviar email en segundo plano
    Thread(target=send_async_email, args=(app, msg)).start()
