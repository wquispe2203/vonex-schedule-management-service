from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User, Role
from app.core.security import get_password_hash
import sys
import os

# Database URL para TEST (URL Encoded)
DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost:5432/schedule_test_db"

def seed():
    print("--- [SEED] Seeding test database ---")
    engine = create_engine(DATABASE_URL)
    
    # Asegurar que las tablas existan
    Base.metadata.create_all(bind=engine)
    
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # 1. Crear Rol SUPERADMIN
        role = db.query(Role).filter(Role.name == "SUPERADMIN").first()
        if not role:
            role = Role(name="SUPERADMIN", is_protected=True)
            db.add(role)
            db.flush()
            print("  - Role SUPERADMIN created.")

        # 2. Crear Usuario Admin
        user = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        if not user:
            user = User(
                username="admin@vonex.edu.pe",
                password_hash=get_password_hash("admin123"),
                is_active=True,
                nombres="Admin",
                apellidos="Test"
            )
            user.roles.append(role)
            db.add(user)
            db.commit()
            print("  - User admin@vonex.edu.pe created.")
        else:
            print("  - User already exists.")

    except Exception as e:
        print(f"[ERROR] Seeding failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
