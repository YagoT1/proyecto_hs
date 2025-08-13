import os # Mantén esto si lo usas para otras cosas, pero no para dotenv
from app import create_app, db # Asegúrate que 'db' se importe si lo necesitas en este archivo
from dotenv import load_dotenv
load_dotenv()

# Crea la app
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Si necesitas crear tablas o inicializar algo con la base de datos, hazlo aquí.
        # Por ejemplo, para crear todas las tablas definidas en tus modelos:
        db.create_all()
        pass

    # Inicia el servidor en otro puerto (esto es para desarrollo local, no para PythonAnywhere)
    app.run(host='0.0.0.0', port=5000, debug=True)
