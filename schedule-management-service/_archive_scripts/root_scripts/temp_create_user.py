import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the app directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.models import User, Role
from app.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def ensure_test_user():
    db = SessionLocal()
    try:
        username = "admin@vonex.edu.pe"
        password = "Admin123"
        hashed_pw = get_password_hash(password)
        
        user = db.query(User).filter(User.username == username).first()
        if user:
            print(f"User {username} already exists. Resetting password...")
            user.password_hash = hashed_pw
            user.is_active = True
        else:
            print(f"Creating user {username}...")
            user = User(
                username=username,
                password_hash=hashed_pw,
                nombres="Admin",
                apellidos="Vonex",
                area="SISTEMAS",
                is_active=True
            )
            db.add(user)
        
        # Ensure role SISTEMAS exists and is assigned
        role = db.query(Role).filter(Role.name == "SISTEMAS").first()
        if not role:
            print("Creating role SISTEMAS...")
            role = Role(name="SISTEMAS")
            db.add(role)
            db.commit()
            db.refresh(role)
        
        if role not in user.roles:
            user.roles.append(role)
            
        db.commit()
        print(f"✅ Success: {username} is ready with password {password}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    ensure_test_user()
