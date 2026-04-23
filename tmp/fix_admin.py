import sys
import os

sys.path.insert(0, r'd:/Desktop/MOD HOR/schedule-management-service')
from app.database import SessionLocal
from app.models import User, Role
from app.core.security import get_password_hash

def fix_admin():
    db = SessionLocal()
    try:
        email = "admin@vonex.edu.pe"
        user = db.query(User).filter(User.username == email).first()
        hashed_pw = get_password_hash("Admin123")
        
        if not user:
            print(f"User {email} not found. Creating it...")
            user = User(
                username=email,
                password_hash=hashed_pw,
                nombres="Administrador",
                apellidos="Vonex",
                is_active=True
            )
            db.add(user)
        else:
            print(f"User {email} found. Updating password...")
            user.password_hash = hashed_pw
            user.is_active = True
            
        # Ensure role 'admin' exists and is assigned
        role = db.query(Role).filter(Role.name == 'ADMIN').first()
        if not role:
            print("Role ADMIN not found. Creating it...")
            role = Role(name="ADMIN")
            db.add(role)
            db.commit()
            db.refresh(role)
            
        if role not in user.roles:
            print("Assigning ADMIN role to user...")
            user.roles.append(role)
            
        db.commit()
        print("Admin user fixed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_admin()
