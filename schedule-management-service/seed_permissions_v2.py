
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Role, Permission, User

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def seed():
    print("--- SEEDING PERMISSIONS v2 ---")
    
    # 1. Definir permisos requeridos
    perms_to_create = [
        {"code": "ver_docentes", "description": "Ver lista de docentes activos y reporte"},
        {"code": "gestionar_docentes", "description": "CRUD completo de docentes y maestra"},
        {"code": "gestionar_usuarios", "description": "Administrar usuarios, roles y permisos"},
    ]
    
    for p in perms_to_create:
        existing = db.query(Permission).filter(Permission.code == p["code"]).first()
        if not existing:
            new_p = Permission(code=p["code"], description=p["description"])
            db.add(new_p)
            print(f"✅ Creado permiso: {p['code']}")
        else:
            print(f"ℹ️ Permiso ya existe: {p['code']}")
    
    db.commit()
    
    # 2. Definir Matriz de Asignación Obligatoria
    # Usaremos códigos para buscar IDs actualizados
    all_perms = {p.code: p for p in db.query(Permission).all()}
    all_roles = {r.name: r for r in db.query(Role).all()}
    
    # ROL: SISTEMAS & SUPERADMIN -> TODOS
    for rname in ["SISTEMAS", "SUPERADMIN"]:
        if rname in all_roles:
            role = all_roles[rname]
            role.permissions = list(all_perms.values())
            print(f"👑 {rname} asignado con TODOS los permisos ({len(all_perms)})")
            
    # ROL: DIRECCION_ACADEMICA
    if "DIRECCION_ACADEMICA" in all_roles:
        da_role = all_roles["DIRECCION_ACADEMICA"]
        da_perms = [
            all_perms["ver_rpt"],
            all_perms["ver_horarios"],
            all_perms["ver_observaciones"],
            all_perms["crear_observaciones"],
            all_perms["ver_docentes"] # El fix crítico
        ]
        da_role.permissions = da_perms
        print(f"📖 DIRECCION_ACADEMICA asignado con {len(da_perms)} permisos")
        
    # ROL: GTH
    if "GTH" in all_roles:
        gth_role = all_roles["GTH"]
        gth_perms = [
            all_perms["ver_rpt"],
            all_perms["ver_horarios"],
            all_perms["ver_docentes"]
        ]
        gth_role.permissions = gth_perms
        print(f"💼 GTH asignado con {len(gth_perms)} permisos")
        
    db.commit()
    print("\n--- SEED COMPLETE ---")

if __name__ == "__main__":
    seed()
    db.close()
