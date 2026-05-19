from app.core.database import SessionLocal
from app.models import User
from app.dependencies.auth import require_permission
from fastapi import HTTPException
import pytest

def test_permissions():
    db = SessionLocal()
    try:
        # Fetch daacademica user
        user = db.query(User).filter(User.username == "daacademica@vonex.edu.pe").first()
        print(f"User: {user.username}")
        roles = [r.name for r in user.roles]
        print(f"Roles: {roles}")
        
        # Check permissions for ver_rpt
        has_ver_rpt = False
        has_ver_docentes = False
        for r in user.roles:
            for p in r.permissions:
                if p.code == "ver_rpt":
                    has_ver_rpt = True
                if p.code == "ver_docentes":
                    has_ver_docentes = True
                    
        print(f"Has 'ver_rpt' permission: {has_ver_rpt}")
        print(f"Has 'ver_docentes' permission: {has_ver_docentes}")
        
        if has_ver_rpt and not has_ver_docentes:
            print("[VERIFIED] User daacademica has ver_rpt but is missing ver_docentes! This will block /api/rpt-planilla/docentes.")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_permissions()
