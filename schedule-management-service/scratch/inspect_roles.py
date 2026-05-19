from app.core.database import SessionLocal
from app.models.user import Role, User
from sqlalchemy import func

db = SessionLocal()
try:
    roles = db.query(Role).all()
    print(f"Total roles in DB: {len(roles)}")
    for r in roles:
        user_count = len(r.users)
        print(f"Role: {r.name}")
        print(f"  - ID: {r.id}")
        print(f"  - Is Protected: {r.is_protected}")
        print(f"  - Assigned Users count: {user_count}")
        for u in r.users:
            print(f"    * User: {u.username}")
        print("-" * 40)
finally:
    db.close()
