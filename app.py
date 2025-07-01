# proyecto_hs/app.py

from app import create_app # Importa la función 'create_app' y la instancia de 'db' desde tu paquete 'app'

# Crea la instancia de la aplicación llamando a la fábrica
app = create_app()

if __name__ == '__main__':
    # Asegúrate de estar dentro del contexto de la aplicación para interactuar con la base de datos
    with app.app_context():
        # Crea todas las tablas de la base de datos definidas en tus modelos (User, Registro)
        # Esto solo creará las tablas si no existen.
        db.create_all()
    # Inicia el servidor de desarrollo de Flask
    # La configuración de DEBUG se obtiene de FLASK_DEBUG en tu .env, a través de create_app()
    app.run()