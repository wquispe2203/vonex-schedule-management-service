import sys
import os
from sqlalchemy.orm import Session

# Añadir ruta para importar correctamente config y modelos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database import SessionLocal
from app.models import Role, Permission, User, user_roles, role_permissions
from app.core.security import get_password_hash

def seed():
    db: Session = SessionLocal()
    print("Iniciando Seed RBAC...")
    
    try:
        # 1. PERMISOS BASE
        base_permissions = [
            {"code": "ver_rpt", "desc": "Ver reportes de planilla"},
            {"code": "exportar_rpt", "desc": "Exportar reportes de planilla"},
            {"code": "subir_xml", "desc": "Subir XML de aSc Horarios"},
            {"code": "ver_horarios", "desc": "Ver grillas de horarios"},
            {"code": "ver_observaciones", "desc": "Ver incidencias y observaciones"},
            {"code": "crear_observaciones", "desc": "Crear incidencias"},
            {"code": "editar_observaciones", "desc": "Editar incidencias"}
        ]
        
        perm_objs = {}
        for p in base_permissions:
            perm = db.query(Permission).filter(Permission.code == p["code"]).first()
            if not perm:
                perm = Permission(code=p["code"], description=p["desc"])
                db.add(perm)
                db.flush()
            perm_objs[p["code"]] = perm
            
        print("Permisos base sincronizados.")

        # 2. ROLES BASE
        base_roles = ["SUPERADMIN", "SISTEMAS", "DIRECCION_ACADEMICA", "GTH"]
        role_objs = {}
        for r in base_roles:
            role = db.query(Role).filter(Role.name == r).first()
            if not role:
                role = Role(name=r)
                db.add(role)
                db.flush()
            role_objs[r] = role
            
        print("Roles base sincronizados.")

        # 3. ASIGNAR PERMISOS A ROLES
        # Nota: SISTEMAS y SUPERADMIN tienen bypass lógico, pero les podemos dar todos opcionalmente.
        # Aquí seguimos la especificación estricta.
        
        dir_acad_perms = ["ver_observaciones", "crear_observaciones", "ver_rpt", "exportar_rpt", "ver_horarios"]
        gth_perms = ["ver_rpt", "ver_horarios"]

        # Limpiar y asignar DIRECCION_ACADEMICA
        dir_acad = role_objs["DIRECCION_ACADEMICA"]
        dir_acad.permissions = [perm_objs[c] for c in dir_acad_perms]
        
        # Limpiar y asignar GTH
        gth = role_objs["GTH"]
        gth.permissions = [perm_objs[c] for c in gth_perms]
        
        # Asignar todo a SISTEMAS y SUPERADMIN por completitud visual
        all_perms = list(perm_objs.values())
        role_objs["SISTEMAS"].permissions = all_perms
        role_objs["SUPERADMIN"].permissions = all_perms

        print("Permisos asignados a los roles.")

        # 4. CREAR USUARIO ADMIN INICIAL
        admin_email = "admin@vonex.edu.pe"
        # Primero revisamos si existe el admin legacy para actualizarlo y evitar fallos de pkey/sequence
        admin_legacy = db.query(User).filter(User.username == "admin").first()
        if admin_legacy:
            admin_legacy.username = admin_email
            admin_legacy.password_hash = get_password_hash("Admin123!")
            admin_legacy.nombres = "Administrador"
            admin_legacy.apellidos = "Sistema"
            admin_legacy.is_active = True
            admin_user = admin_legacy
            print(f"Usuario legacy 'admin' promovido a {admin_email}.")
        else:
            admin_user = db.query(User).filter(User.username == admin_email).first()
            if not admin_user:
                try:
                    admin_user = User(
                        username=admin_email,
                        password_hash=get_password_hash("Admin123!"), # Password por defecto
                        nombres="Administrador",
                        apellidos="Sistema",
                        is_active=True
                    )
                    db.add(admin_user)
                    db.flush()
                    print(f"Usuario {admin_email} creado.")
                except Exception as ex:
                    if "UniqueViolation" in str(ex) and "users_pkey" in str(ex):
                        db.rollback()
                        print("Fallo de secuencia PostgreSQL detectado. Sincronizando secuencia...")
                        db.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 0) + 1, false) FROM users;"))
                        db.commit()
                        db.add(admin_user)
                        db.flush()
                        print(f"Usuario {admin_email} creado tras sync.")
                    else:
                        raise ex
            else:
                admin_user.password_hash = get_password_hash("Admin123!")
                print(f"Usuario {admin_email} ya existía. Contraseña restablecida.")
            
        # Asignar rol SISTEMAS
        sistemas_role = role_objs["SISTEMAS"]
        if sistemas_role not in admin_user.roles:
            admin_user.roles.append(sistemas_role)
            print(f"Rol SISTEMAS asignado a {admin_email}.")

        db.commit()
        print("Seed completado exitosamente.")

    except Exception as e:
        db.rollback()
        print(f"Error durante el seed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
