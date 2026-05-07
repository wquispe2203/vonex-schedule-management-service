import os
import sys
import re
import json
import logging
from datetime import datetime, timezone
from uuid import UUID
from typing import Optional

# Configurar logging para JSON si es necesario, pero aquí usaremos prints para stdout 12-factor
logging.basicConfig(level=logging.INFO, format='%(message)s')

# Asegurar que el path del proyecto esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.database import SessionLocal
    from app.models.user import User, Role, Permission, user_roles, role_permissions
    from app.core.security import get_password_hash
    from sqlalchemy import insert, select, delete
except ImportError as e:
    print(json.dumps({
        "event": "admin_provisioning_error",
        "error": f"Error de importación: {str(e)}. Asegúrese de ejecutar desde la raíz del proyecto.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))
    sys.exit(1)

def validate_password_complexity(password: str) -> bool:
    """
    Valida complejidad: 8+ caracteres, min 1 mayúscula, 1 minúscula, 1 número y 1 símbolo.
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[ !@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True

def provision_admin():
    # 1. Obtener contraseña desde variable de entorno
    password = os.environ.get("ADMIN_PASSWORD")
    if not password:
        print(json.dumps({
            "event": "admin_provisioning_error",
            "error": "La variable de entorno ADMIN_PASSWORD no está definida.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        sys.exit(1)

    # 2. Validar complejidad
    if not validate_password_complexity(password):
        print(json.dumps({
            "event": "admin_provisioning_error",
            "error": "La contraseña no cumple con los requisitos de complejidad (8+ chars, Mayús, Minús, Número, Símbolo).",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        sys.exit(1)

    db = SessionLocal()
    try:
        # --- ATOMIC TRANSACTION ---
        with db.begin():
            # 3. Garantizar Rol SUPERADMIN
            role = db.query(Role).filter(Role.name == "SUPERADMIN").first()
            if not role:
                role = Role(name="SUPERADMIN")
                db.add(role)
                db.flush()
                # print(f"Role SUPERADMIN created: {role.id}")

            # 4. Vincular TODOS los permisos al rol SUPERADMIN
            all_perms = db.query(Permission).all()
            # Limpiar permisos previos del rol para asegurar consistencia total
            db.execute(delete(role_permissions).where(role_permissions.c.role_id == role.id))
            
            if all_perms:
                ins_perms = [
                    {"role_id": role.id, "permission_id": p.id} for p in all_perms
                ]
                db.execute(insert(role_permissions), ins_perms)

            # 5. Buscar Usuario
            admin_username = "admin@vonex.edu.pe"
            user = db.query(User).filter(User.username == admin_username).first()
            
            action = "RESET" if user else "CREATE"
            hashed = get_password_hash(password)

            if not user:
                user = User(
                    username=admin_username,
                    password_hash=hashed,
                    nombres="Admin",
                    apellidos="UAT",
                    is_active=True
                )
                db.add(user)
                db.flush()
            else:
                user.password_hash = hashed
                user.is_active = True

            # 6. Vincular Usuario a Rol
            # Verificar si ya tiene el rol
            has_role = db.execute(
                select(user_roles).where(
                    user_roles.c.user_id == user.id,
                    user_roles.c.role_id == role.id
                )
            ).first()
            
            if not has_role:
                db.execute(insert(user_roles).values(user_id=user.id, role_id=role.id))

        # --- ÉXITO ---
        print(json.dumps({
            "event": "admin_provisioning_success",
            "action": action,
            "username": admin_username,
            "role": "SUPERADMIN",
            "permissions_linked": len(all_perms),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mdm_version": "v4.2"
        }))

    except Exception as e:
        print(json.dumps({
            "event": "admin_provisioning_error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }))
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    provision_admin()
