import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.database import engine, SessionLocal
from app.models import User, Role, Permission
from app.core.security import get_password_hash

def reseed_admin():
    print(f"--- [DATABASE CONFIG] Conectado en runtime a: {engine.url} ---")
    
    db = SessionLocal()
    try:
        target_username = "admin_test@vonex.edu.pe"
        
        # 1. Limpieza controlada
        existing_user = db.query(User).filter(User.username == target_username).first()
        if existing_user:
            print(f"Limpiando usuario existente: {target_username}")
            db.delete(existing_user)
            db.commit()
            
        # 2. Asegurar Rol SISTEMAS
        role_sistemas = db.query(Role).filter(Role.name == "SISTEMAS").first()
        if not role_sistemas:
            role_sistemas = Role(name="SISTEMAS")
            db.add(role_sistemas)
            db.flush()
        
        # 3. Seed de Usuario
        print(f"Creando usuario {target_username}...")
        new_admin = User(
            username=target_username,
            password_hash=get_password_hash("TestAdmin123!"),
            nombres="Admin",
            apellidos="Test",
            is_active=True
        )
        new_admin.roles.append(role_sistemas)
        db.add(new_admin)
        db.commit()
        
        print("SUCCESS: Usuario admin_test@vonex.edu.pe creado con exito.")
        
    except Exception as e:
        db.rollback()
        print(f"ERROR: Error insertando datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reseed_admin()
