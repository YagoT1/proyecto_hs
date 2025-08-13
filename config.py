import os

class Config:
    # ¡IMPORTANTE! CLAVE SECRETA HARDCODEADA SOLO PARA DEPURACIÓN.
    # CAMBIAR ESTO POR UNA VARIABLE DE ENTORNO EN PRODUCCIÓN REAL.
    SECRET_KEY = 'una_clave_seg333c8fbc55725e02af22c87f4512ec8273cad72d7648939dura_aleatoria_gG9!pQz@7Rk$2tY&5uV*8wX'
    
    # Configuración de la base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Recicla las conexiones a la base de datos después de 1 hora (3600 segundos)
    SQLALCHEMY_POOL_RECYCLE = 3600 

    # Hace ping a la conexión antes de usarla para verificar si está viva
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Configuración para subida de archivos
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 

    # Configuración de Flask-Mail
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.googlemail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'tu_email@ejemplo.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'tu_contraseña_de_aplicacion_o_clave_segura'
    ADMINS = ['tu_email_admin@ejemplo.com']

    # ¡MODIFICADO! Obtiene la URL de recibos de sueldo desde las variables de entorno
    RECIBOS_SUELDO = os.environ.get('RECIBOS_SUELDO')
