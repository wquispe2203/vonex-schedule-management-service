from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- Users ---")
    users = db.execute(text("SELECT id, username, is_active FROM users")).fetchall()
    for u in users:
        print(u)
        
    print("\n--- User Roles ---")
    user_roles = db.execute(text("""
        SELECT u.username, r.name 
        FROM users u 
        JOIN user_roles ur ON u.id = ur.user_id 
        JOIN roles r ON ur.role_id = r.id
    """)).fetchall()
    for ur in user_roles:
        print(ur)

    print("\n--- Role Permissions ---")
    role_perms = db.execute(text("""
        SELECT r.name, p.code 
        FROM roles r 
        JOIN role_permissions rp ON r.id = rp.role_id 
        JOIN permissions p ON rp.permission_id = p.id
    """)).fetchall()
    for rp in role_perms:
        print(rp)
finally:
    db.close()
