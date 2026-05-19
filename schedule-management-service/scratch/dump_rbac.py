import sys
import os
# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db, SessionLocal
from app.models.user import Role, Permission

db = SessionLocal()
try:
    print("--- ROLES ---")
    roles = db.query(Role).all()
    for r in roles:
        perms = [p.code for p in r.permissions]
        print(f"- Role: {r.name} ({r.id}) -> Perms: {perms}")
        
    print("\n--- ALL PERMISSIONS ---")
    all_perms = db.query(Permission).all()
    for p in all_perms:
        print(f"- Code: {p.code} | Desc: {p.description}")
finally:
    db.close()
