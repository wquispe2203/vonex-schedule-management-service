from app.database import SessionLocal
from app.models import User, Role, Permission

def grant_all_to_admin():
    db = SessionLocal()
    try:
        # 1. Obtener todos los permisos
        all_permissions = db.query(Permission).all()
        print(f"Encontrados {len(all_permissions)} permisos.")

        # 2. Obtener rol SISTEMAS
        sistemas_role = db.query(Role).filter(Role.name == "SISTEMAS").first()
        if not sistemas_role:
            print("Rol SISTEMAS no encontrado. Creando...")
            sistemas_role = Role(name="SISTEMAS")
            db.add(sistemas_role)
            db.flush()

        # 3. Vincular todos los permisos al rol SISTEMAS
        # Limpiamos existentes para asegurar full sync
        sistemas_role.permissions = all_permissions
        print(f"Vinculados {len(all_permissions)} permisos al rol SISTEMAS.")

        # 4. Asegurar que admin@vonex.edu.pe tenga el rol SISTEMAS
        admin_user = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        if admin_user:
            if sistemas_role not in admin_user.roles:
                admin_user.roles.append(sistemas_role)
                print("Rol SISTEMAS asignado a admin@vonex.edu.pe")
            else:
                print("admin@vonex.edu.pe ya tiene el rol SISTEMAS")
        else:
            print("ERROR: admin@vonex.edu.pe no encontrado")

        db.commit()
        print("Pre-condición de seguridad completada con éxito.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    grant_all_to_admin()
