# set_admin.py
# Este script debe ejecutarse desde la raíz de tu proyecto (donde está la carpeta 'app')

from app import create_app, db
from app.models import User

# Crea la instancia de la aplicación llamando a la función de fábrica
app = create_app()

with app.app_context():
    # --- CONFIGURACIÓN DE USUARIOS ---
    # ¡IMPORTANTE! Cambia estos nombres de usuario por los reales en tu base de datos.
    owner_username = 'Yago Torres' # <--- CAMBIA ESTO por tu usuario principal
    admin_username = 'NombreUsuarioAdmin'   # <--- CAMBIA ESTO por un usuario que será solo admin
    moderator_username = 'NombreUsuarioModerador' # <--- CAMBIA ESTO por un usuario que será solo moderador

    print("--- Asignando Roles ---")

    # 1. Asignar rol de OWNER (el CEO/dueño de la app)
    owner_user = User.query.filter_by(username=owner_username).first()
    if owner_user:
        owner_user.is_owner = True
        owner_user.is_admin = True # El owner también es un administrador completo
        owner_user.is_moderator = True # Y también un moderador
        db.session.commit()
        print(f"Usuario '{owner_user.username}' ahora es OWNER, ADMIN y MODERADOR.")
    else:
        print(f"Error: Usuario OWNER '{owner_username}' no encontrado. Asegúrate de que el usuario exista en la base de datos.")

    # 2. Asignar rol de ADMIN (si no es el owner)
    if admin_username and admin_username != owner_username:
        admin_user = User.query.filter_by(username=admin_username).first()
        if admin_user:
            if not admin_user.is_owner: # Solo si no es el owner
                admin_user.is_admin = True
                admin_user.is_moderator = True # Un admin también es moderador
                db.session.commit()
                print(f"Usuario '{admin_user.username}' ahora es ADMIN y MODERADOR.")
            else:
                print(f"Advertencia: El usuario '{admin_username}' ya es el OWNER. No se necesita asignar el rol de ADMIN por separado.")
        else:
            print(f"Error: Usuario ADMIN '{admin_username}' no encontrado.")

    # 3. Asignar rol de MODERADOR (si no es admin ni owner)
    if moderator_username and moderator_username != owner_username and moderator_username != admin_username:
        moderator_user = User.query.filter_by(username=moderator_username).first()
        if moderator_user:
            if not moderator_user.is_admin and not moderator_user.is_owner: # Solo si no es admin ni owner
                moderator_user.is_moderator = True
                db.session.commit()
                print(f"Usuario '{moderator_user.username}' ahora es MODERADOR.")
            else:
                print(f"Advertencia: El usuario '{moderator_username}' ya es un administrador o el owner. No se necesita asignar el rol de MODERADOR por separado.")
        else:
            print(f"Error: Usuario MODERADOR '{moderator_username}' no encontrado.")

    print("--- Proceso de asignación de roles completado ---")

