from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Teacher, Role, User
import uuid

def verify_uuid_architecture():
    db = SessionLocal()
    try:
        print("--- VERIFICACIÓN DE ARQUITECTURA UUID ---")
        
        # 1. Verificar Teacher
        teacher = db.query(Teacher).first()
        if teacher:
            print(f"Teacher ID: {teacher.id} (Type: {type(teacher.id)})")
            print(f"Teacher legacy_id: {teacher.legacy_id}")
            assert isinstance(teacher.id, uuid.UUID)
        
        # 2. Verificar Relación User-Role (Intermediate Table)
        user = db.query(User).first()
        if user:
            print(f"User ID: {user.id} (Type: {type(user.id)})")
            roles = user.roles
            print(f"User has {len(roles)} roles.")
            for r in roles:
                print(f"  Role: {r.name} (ID: {r.id})")
        
        print("\n[SUCCESS] La arquitectura UUID es consistente en el ORM.")
        
    except Exception as e:
        print(f"\n[FAILURE] Error en verificación: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_uuid_architecture()
