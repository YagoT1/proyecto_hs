from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(email='eve172013@gmail.com').first()
    if user:
        user.is_active = True
        db.session.commit()
        print("Usuario activado correctamente.")
    else:
        print("Usuario no encontrado.")
