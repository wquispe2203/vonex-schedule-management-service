from app.core.database import SessionLocal
from app.models import User
db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"User: {u.username} | Active: {u.is_active}")
db.close()
