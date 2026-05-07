import sys
import os

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import SessionLocal
from app.models import User

def create_admin():
    db = SessionLocal()
    try:
        # Revisa si ya existe el usuario 1
        existing_user = db.query(User).filter(User.id == 1).first()
        if existing_user:
            print("El usuario administrador (ID=1) ya existe.")
            return

        # Crea un usuario administrador por defecto
        admin_user = User(
            id=1,
            username="admin",
            password_hash="admin_hash_dummy_password", 
            role="admin"
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        print(f"Usuario Creado Exitosamente: ID={admin_user.id}, Username={admin_user.username}")
        
    except Exception as e:
        db.rollback()
        print(f"Error al crear el usuario: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
