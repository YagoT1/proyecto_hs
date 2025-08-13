import pymysql
import os

# --- CONFIGURACIÓN DE TU BASE DE DATOS MySQL ---
# ¡Asegúrate de que estos valores sean EXACTAMENTE los de tu panel de PythonAnywhere!
DB_HOST = 'yaguito19.mysql.pythonanywhere-services.com'
DB_USER = 'yaguito19$proyectohs' # Tu usuario de MySQL (que incluye tu nombre de usuario de PA)
DB_PASSWORD = 'Pyth0nAnywh3r3DbP4ssw0rd!2025' # Tu contraseña de MySQL
DB_NAME = 'yaguito19$proyectohs' # Tu nombre de base de datos MySQL (que incluye tu nombre de usuario de PA)

# Si tienes las variables de entorno configuradas en PythonAnywhere, puedes usarlas así:
# DB_HOST = os.environ.get('DB_HOST', 'yaguito19.mysql.pythonanywhere-services.com')
# DB_USER = os.environ.get('DB_USER', 'yaguito19$proyectohs')
# DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Pyth0nAnywh3r3DbP4ssw0rd!2025')
# DB_NAME = os.environ.get('DB_NAME', 'yaguito19$proyectohs')


print(f"Intentando conectar a MySQL:")
print(f"  Host: {DB_HOST}")
print(f"  User: {DB_USER}")
print(f"  DB Name: {DB_NAME}")
print(f"  Password: {'*' * len(DB_PASSWORD) if DB_PASSWORD else 'None'}") # No mostrar la contraseña real

try:
    # Intenta establecer la conexión
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    print("\n¡Conexión a MySQL exitosa!")

    with connection.cursor() as cursor:
        # Ejecuta un comando para listar las tablas
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("\nTablas en la base de datos:")
        if tables:
            for table in tables:
                print(f"- {list(table.values())[0]}") # Acceder al valor del diccionario
            
            # Si la tabla 'user' existe, intenta describirla y obtener algunos datos
            if {'Tables_in_yaguito19$proyectohs': 'user'} in tables or {'Tables_in_yaguito19$proyectohs': b'user'} in tables: # Ajusta el nombre de la DB según tu salida
                print("\nTabla 'user' encontrada. Describiendo su estructura:")
                cursor.execute("DESCRIBE user;")
                user_table_desc = cursor.fetchall()
                for col in user_table_desc:
                    print(f"  - {col['Field']} ({col['Type']})")
                
                print("\nPrimeros 5 usuarios (id, username, email):")
                cursor.execute("SELECT id, username, email FROM user LIMIT 5;")
                users = cursor.fetchall()
                if users:
                    for user in users:
                        print(f"  - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
                else:
                    print("  No hay usuarios en la tabla 'user'.")
            else:
                print("\nLa tabla 'user' NO fue encontrada en la base de datos.")

        else:
            print("No se encontraron tablas en la base de datos.")

except pymysql.Error as e:
    print(f"\n¡Error al conectar o interactuar con MySQL! Detalles del error:")
    print(f"  Código de error: {e.args[0]}")
    print(f"  Mensaje de error: {e.args[1]}")
    print(f"Por favor, verifica el host, usuario, contraseña y nombre de la base de datos.")
except Exception as e:
    print(f"\nOcurrió un error inesperado: {e}")
finally:
    if 'connection' in locals() and connection.open:
        connection.close()
        print("\nConexión a MySQL cerrada.")

