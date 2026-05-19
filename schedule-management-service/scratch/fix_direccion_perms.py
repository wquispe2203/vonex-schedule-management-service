import sys
import os

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, SessionLocal
from app.models.user import Role, Permission

db = SessionLocal()
try:
    # Find role DIRECCION (checking multiple common forms due to encoding)
    roles = db.query(Role).all()
    role_dir = None
    for r in roles:
        rname = r.name.upper()
        if "DIRECCI" in rname or rname == "DIRECCIÓN" or rname == "DIRECCION":
            role_dir = r
            break
            
    if not role_dir:
        print("[ERROR] DIRECCION role not found!")
        sys.exit(1)
        
    print(f"[INFO] Found DIRECCION role with ID: {role_dir.id}, Internal Name: {role_dir.name}")
    
    # Find permission crear_observaciones
    perm_crear = db.query(Permission).filter(Permission.code == "crear_observaciones").first()
    if not perm_crear:
        print("[ERROR] Permission crear_observaciones not found!")
        sys.exit(1)
        
    # Check if permission is assigned and remove it
    if perm_crear in role_dir.permissions:
        role_dir.permissions.remove(perm_crear)
        db.commit()
        print("[SUCCESS] Removed crear_observaciones from DIRECCION role!")
    else:
        print("[INFO] DIRECCION role does not have crear_observaciones assigned.")
        
    # Verify remaining perms
    db.refresh(role_dir)
    print(f"[INFO] Remaining permissions for DIRECCION: {[p.code for p in role_dir.permissions]}")
    
finally:
    db.close()
