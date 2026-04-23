from app.database import SessionLocal
from app.models import Role, Permission, User

def fix_permissions_uat():
    db = SessionLocal()
    try:
        # 1. Definir todos los permisos requeridos por el sistema
        required_perms = [
            "ver_rpt", "exportar_rpt", "subir_xml", "ver_horarios", 
            "ver_observaciones", "crear_observaciones", "editar_observaciones",
            "gestionar_usuarios", "ver_docentes", "gestionar_docentes", 
            "gestionar_configuracion"
        ]
        
        # 2. Asegurar que existan en la tabla Permission
        for code in required_perms:
            perm = db.query(Permission).filter(Permission.code == code).first()
            if not perm:
                print(f"Creando permiso faltante: {code}")
                perm = Permission(code=code)
                db.add(perm)
        db.flush()
        
        # 3. Vincular todos al rol SISTEMAS
        all_perms = db.query(Permission).filter(Permission.code.in_(required_perms)).all()
        sistemas_role = db.query(Role).filter(Role.name == "SISTEMAS").first()
        if sistemas_role:
            sistemas_role.permissions = all_perms
            print(f"Vinculados {len(all_perms)} permisos al rol SISTEMAS.")
        
        # 4. Asegurar que admin tenga el rol
        admin = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        if admin and sistemas_role not in admin.roles:
            admin.roles.append(sistemas_role)
            print("Rol SISTEMAS verificado para admin@vonex.edu.pe")
            
        db.commit()
        print("Regularización de permisos completada.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_permissions_uat()
