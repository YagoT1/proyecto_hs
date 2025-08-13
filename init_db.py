from app import create_app, db

if __name__ == "__main__":
    db_url = "mysql+pymysql://yaguito19:Pyth0nAnywh3r3DbP4ssw0rd!2025@yaguito19.mysql.pythonanywhere-services.com/yaguito19$proyectohs"
    app = create_app(db_url=db_url)
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas correctamente.")
