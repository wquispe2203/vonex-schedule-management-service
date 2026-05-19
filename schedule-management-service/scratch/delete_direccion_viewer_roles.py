import sys
from app.core.database import SessionLocal
from app.models.user import Role
from sqlalchemy import text

print("Starting deletion of DIRECCION and VIEWER roles from the database...")

db = SessionLocal()
try:
    # 1. Find the roles by name
    target_names = ["DIRECCION", "DIRECCIÓN", "DIRECCION_ACADEMICA", "VIEWER"]
    roles_to_delete = db.query(Role).filter(Role.name.in_(target_names)).all()
    
    print(f"Found {len(roles_to_delete)} roles to delete: {[r.name for r in roles_to_delete]}")
    
    if roles_to_delete:
        role_ids = [str(r.id) for r in roles_to_delete]
        
        # Delete associations from user_roles
        print("Cleaning user_roles associations...")
        user_roles_deleted = db.execute(
            text("DELETE FROM user_roles WHERE role_id::text IN :ids"),
            {"ids": tuple(role_ids)}
        ).rowcount
        print(f"Deleted {user_roles_deleted} user-role associations.")

        # Delete associations from role_permissions
        print("Cleaning role_permissions associations...")
        role_perms_deleted = db.execute(
            text("DELETE FROM role_permissions WHERE role_id::text IN :ids"),
            {"ids": tuple(role_ids)}
        ).rowcount
        print(f"Deleted {role_perms_deleted} role-permission associations.")

        # Delete the roles
        print("Deleting the roles from 'roles' table...")
        roles_deleted = db.execute(
            text("DELETE FROM roles WHERE id::text IN :ids"),
            {"ids": tuple(role_ids)}
        ).rowcount
        print(f"Deleted {roles_deleted} roles.")
        
        db.commit()
        print("Transaction successfully committed.")
    else:
        print("No matching roles found to delete.")

    # 2. Check remaining roles
    remaining_roles = db.query(Role).all()
    print("\nVerification - Remaining roles in DB:")
    for r in remaining_roles:
        print(f"- {r.name} (ID: {r.id}, Is Protected: {r.is_protected})")

except Exception as e:
    db.rollback()
    print(f"ERROR: Transaction rolled back. Details: {e}")
    sys.exit(1)
finally:
    db.close()
