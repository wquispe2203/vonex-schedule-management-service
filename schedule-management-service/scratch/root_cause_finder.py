import sys
import os
import traceback
from uuid import UUID
from sqlalchemy.orm import Session, joinedload

# Asegurar que el path incluya la app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User, Role, Permission, BreakConfig, LunchConfig, Teacher
from app.modules.horarios import repository as horarios_repo
from app.modules.configuracion import service as config_service

def diagnose_all():
    db = SessionLocal()
    print("--- ROOT CAUSE DEEP DIAGNOSTIC ---")
    
    # 1. Diagnóstico Auth / User Me
    print("\n1. Testing Auth User Hydration (Admin)")
    try:
        admin = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        if not admin:
            print("ERROR: Admin user not found for testing")
        else:
            print(f"User found: {admin.id}")
            # Simulando la query de get_current_user con joinedload
            user = db.query(User).options(
                joinedload(User.roles).joinedload(Role.permissions)
            ).filter(User.id == admin.id).first()
            print(f"SUCCESS: User Hydration successful. Roles: {[r.name for r in user.roles]}")
    except Exception as e:
        print("FAILURE IN /api/users/me (Auth Layer)")
        traceback.print_exc()

    # 2. Diagnóstico Configuración
    print("\n2. Testing Configuration (Recesos)")
    try:
        # Check if list_recesses exists and works
        if hasattr(config_service, 'list_recesses'):
            recesses = config_service.list_recesses(db)
            print(f"SUCCESS: list_recesses successful. Count: {len(recesses)}")
        else:
            print("ERROR: config_service.list_recesses MISSING")
            
        print("\nTesting Configuration (Almuerzos)")
        if hasattr(config_service, 'list_lunches'):
            lunches = config_service.list_lunches(db)
            print(f"SUCCESS: list_lunches successful. Count: {len(lunches)}")
        else:
            print("ERROR: config_service.list_lunches MISSING")
            
    except Exception as e:
        print("FAILURE IN /api/config/recesos or almuerzos")
        traceback.print_exc()

    # 3. Diagnóstico Horarios / Teachers
    print("\n3. Testing Teacher List")
    try:
        teachers = horarios_repo.fetch_all_teachers(db)
        print(f"SUCCESS: fetch_all_teachers successful. Count: {len(teachers)}")
        # Check if t.id works (mapped from t.uid previously)
        processed = [{"id": str(t.id), "name": f"{t.first_name} {t.last_name}"} for t in teachers]
        print(f"SUCCESS: Teacher mapping successful.")
    except Exception as e:
        print("FAILURE IN /api/schedule/teachers")
        traceback.print_exc()

    db.close()

if __name__ == "__main__":
    diagnose_all()
