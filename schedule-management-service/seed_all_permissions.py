import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure the app module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.models import Role, Permission, User
from app.database import SQLALCHEMY_DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed():
    print("--- FULL PERMISSION SEEDING ---")
    
    # List of ALL permissions used in the codebase
    perms_to_ensure = [
        # Reportes
        {"code": "ver_rpt", "description": "Ver reporte de planillas"},
        {"code": "exportar_rpt", "description": "Exportar reporte a Excel"},
        
        # Docentes
        {"code": "ver_docentes", "description": "Ver lista de docentes y maestra"},
        {"code": "gestionar_docentes", "description": "Crear, editar y fusionar docentes"},
        
        # Horarios (XML Upload)
        {"code": "ver_horarios", "description": "Ver visor de horarios"},
        {"code": "subir_xml", "description": "Cargar archivos XML al sistema"},
        
        # Observaciones
        {"code": "ver_observaciones", "description": "Ver logs de incidencias"},
        {"code": "crear_observaciones", "description": "Registrar nuevas incidencias"},
        {"code": "editar_observaciones", "description": "Eliminar o modificar incidencias"},
        
        # Usuarios & RBAC
        {"code": "gestionar_usuarios", "description": "Administrar usuarios y roles"},
        {"code": "gestionar_configuracion", "description": "Administrar recesos y almuerzos"},
    ]
    
    for p in perms_to_ensure:
        existing = db.query(Permission).filter(Permission.code == p["code"]).first()
        if not existing:
            new_p = Permission(code=p["code"], description=p["description"])
            db.add(new_p)
            print(f"✅ Created permission: {p['code']}")
        else:
            existing.description = p["description"] # Update description
            print(f"ℹ️ Permission exists: {p['code']}")
    
    db.commit()
    
    # 2. Assign to Roles
    all_perms = {p.code: p for p in db.query(Permission).all()}
    all_roles = {r.name: r for r in db.query(Role).all()}
    
    # Admin roles -> All permissions
    for rname in ["SISTEMAS", "SUPERADMIN"]:
        if rname in all_roles:
            role = all_roles[rname]
            role.permissions = list(all_perms.values())
            print(f"👑 {rname} assigned with ALL permissions ({len(all_perms)})")
            
    # DIRECCION_ACADEMICA role -> Specific permissions
    if "DIRECCION_ACADEMICA" in all_roles:
        da_role = all_roles["DIRECCION_ACADEMICA"]
        da_perms = [
            all_perms["ver_rpt"],
            all_perms["ver_horarios"],
            all_perms["ver_observaciones"],
            all_perms["crear_observaciones"],
            all_perms["ver_docentes"]
        ]
        # REGLA CRÍTICA: NO debe tener subir_xml ni gestionar_usuarios ni gestionar_docentes
        da_role.permissions = da_perms
        print(f"📖 DIRECCION_ACADEMICA assigned with {len(da_perms)} permissions (Restricted)")
        
    db.commit()
    print("\n--- SEED COMPLETE ---")

if __name__ == "__main__":
    seed()
    db.close()
