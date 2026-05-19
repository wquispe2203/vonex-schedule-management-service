from app.core.database import SessionLocal
from app.models import User, Role, Permission

def run():
    print("=== RBAC FORENSIC AUDIT ===")
    db = SessionLocal()
    try:
        # 1. Users list
        users = db.query(User).all()
        print(f"\nTotal Users: {len(users)}")
        for u in users:
            roles = [r.name for r in u.roles]
            print(f"  - Username: {u.username}, Name: {u.nombres} {u.apellidos}, Active: {u.is_active}, Roles: {roles}")
            
        # 2. Roles and Permissions mapping
        roles_db = db.query(Role).all()
        print(f"\nTotal Roles: {len(roles_db)}")
        for r in roles_db:
            perms = [p.code for p in r.permissions]
            print(f"  - Role: {r.name}, Permissions: {perms}")
            
        # 3. Permissions list
        perms_db = db.query(Permission).all()
        print(f"\nTotal Permissions: {len(perms_db)}")
        for p in perms_db:
            print(f"  - Permission Code: {p.code}, Desc: {p.description}")
            
    finally:
        db.close()
        print("\n=== RBAC FORENSIC AUDIT COMPLETE ===")

if __name__ == "__main__":
    run()
