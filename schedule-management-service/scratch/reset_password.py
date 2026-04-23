import sys
import os
from sqlalchemy.orm import Session

# Ajustar el path para importar app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

def reset_admin_password():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        if not user:
            print("Usuario admin@vonex.edu.pe no encontrado")
            return
        
        new_password = "admin"
        user.password_hash = get_password_hash(new_password)
        db.commit()
        print(f"Contraseña de {user.username} reseteada a '{new_password}'")
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin_password()
