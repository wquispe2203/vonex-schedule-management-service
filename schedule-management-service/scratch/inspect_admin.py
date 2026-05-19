from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
try:
    user = db.query(User).first()
    if user:
        print("First user returned by db.query(User).first():")
        print("Username:", user.username)
        print("Roles:", [r.name for r in user.roles])
        print("Is active:", user.is_active)
    else:
        print("No users found!")
finally:
    db.close()
