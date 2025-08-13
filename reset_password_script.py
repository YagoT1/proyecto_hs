# reset_password_script.py
import os
from app import create_app, db, bcrypt # Importamos create_app, db y bcrypt
from app.models import User # Importamos el modelo User

# Crea una instancia de la aplicación Flask
# Esto cargará tu configuración (incluyendo SECRET_KEY) y las extensiones
app = create_app()

# Asegúrate de estar dentro del contexto de la aplicación
with app.app_context():
    # Email del usuario cuya contraseña quieres restablecer
    user_email_to_reset = 'eve172013@gmail.com' # ¡CAMBIA ESTO SI ES OTRO USUARIO!
    new_password = '99368203.Eve' # ¡CAMBIA ESTO POR UNA CONTRASEÑA NUEVA Y SEGURA!

    print(f"Buscando usuario con email: {user_email_to_reset}")
    user = User.query.filter_by(email=user_email_to_reset).first()

    if user:
        print(f"Usuario encontrado: {user.username}")
        # Hashea la nueva contraseña usando bcrypt
        user.set_password(new_password) # Usa el método set_password del modelo User
        db.session.commit()
        print(f"Contraseña para {user.username} ({user.email}) ha sido restablecida exitosamente.")
        print(f"¡Ahora intenta iniciar sesión con la nueva contraseña: '{new_password}'")
    else:
        print(f"Error: No se encontró ningún usuario con el email '{user_email_to_reset}'.")
        print("Asegúrate de que el email sea correcto y que el usuario exista en la base de datos.")
