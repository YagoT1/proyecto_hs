from app import create_app, db
from app.models import User
from dotenv import load_dotenv
import os

# Carga las variables del archivo .env
load_dotenv()

# Obtiene la URL de base de datos y los usuarios desde variables de entorno
db_url = os.getenv("DATABASE_URL")
owner_username = os.getenv("OWNER")
admin_username = os.getenv("ADMIN")
moderator_username = os.getenv("MOD")

# Crea la instancia de la aplicación pasando la URL de la base de datos
app = create_app(db_url=db_url)

with app.app_context():
    print("--- Asignando Roles ---")

    owner_user = User.query.filter_by(username=owner_username).first()
    if owner_user:
        owner_user.is_owner = True
        owner_user.is_admin = True
        owner_user.is_moderator = True
        db.session.commit()
        print(f"Usuario '{owner_user.username}' ahora es OWNER, ADMIN y MODERADOR.")
    else:
        print(f"Error: Usuario OWNER '{owner_username}' no encontrado.")

    if admin_username and admin_username != owner_username:
        admin_user = User.query.filter_by(username=admin_username).first()
        if admin_user:
            if not admin_user.is_owner:
                admin_user.is_admin = True
                admin_user.is_moderator = True
                db.session.commit()
                print(f"Usuario '{admin_user.username}' ahora es ADMIN y MODERADOR.")
            else:
                print(f"Advertencia: El usuario '{admin_username}' ya es OWNER.")
        else:
            print(f"Error: Usuario ADMIN '{admin_username}' no encontrado.")

    if moderator_username and moderator_username != owner_username and moderator_username != admin_username:
        moderator_user = User.query.filter_by(username=moderator_username).first()
        if moderator_user:
            if not moderator_user.is_admin and not moderator_user.is_owner:
                moderator_user.is_moderator = True
                db.session.commit()
                print(f"Usuario '{moderator_user.username}' ahora es MODERADOR.")
            else:
                print(f"Advertencia: El usuario '{moderator_username}' ya es ADMIN o OWNER.")
        else:
            print(f"Error: Usuario MODERADOR '{moderator_username}' no encontrado.")

    print("--- Proceso de asignación de roles completado ---")
