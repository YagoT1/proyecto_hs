import os
from dotenv import load_dotenv # Importa load_dotenv

# Carga las variables de entorno desde el archivo .env
# ¡Esto debe ser lo primero que se ejecute!
load_dotenv()

from app import create_app, db # Importa la función 'create_app' y la instancia de 'db' desde tu paquete 'app'

# Crea la instancia de la aplicación llamando a la fábrica
app = create_app()

if __name__ == '__main__':
    # Asegúrate de estar dentro del contexto de la aplicación para interactuar con la base de datos
    with app.app_context():
        # db.create_all() # COMENTAR O ELIMINAR: Flask-Migrate se encargará de esto
        pass # Puedes dejarlo vacío o eliminar el 'with' si no necesitas db.create_all()

    # Inicia el servidor de desarrollo de Flask
    # La configuración de DEBUG se obtiene de FLASK_DEBUG en tu .env, a través de create_app()
    app.run()
