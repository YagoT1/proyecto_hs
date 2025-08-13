# wsgi.py
# Este archivo es para que Flask-CLI y Flask-Migrate puedan encontrar tu aplicación.

import os
import sys

# Añade la ruta de tu proyecto al sys.path
# Asegúrate de que '/home/yaguito19/proyecto_hs' sea la ruta correcta a la raíz de tu proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa tu función create_app y tus instancias de db y migrate
from app import create_app, db, migrate

# Crea la instancia de la aplicación
# Flask-Migrate necesita que la aplicación esté creada para registrar los comandos 'db'
application = create_app()

# Asegúrate de que Flask-Migrate esté inicializado con la aplicación y la instancia de db
# Esto ya debería ocurrir dentro de create_app(), pero lo re-afirmamos aquí por claridad
# y para asegurar que el contexto de la CLI lo vea.
migrate.init_app(application, db)
