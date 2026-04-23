
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Role, Permission, User

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:C%40rden4s2k24@localhost/schedule_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("--- ROLES ---")
roles = db.query(Role).all()
for r in roles:
    perms = [p.code for p in r.permissions]
    print(f"Role: {r.name} (ID: {r.id}) - Permissions: {perms}")

print("\n--- PERMISSIONS ---")
perms = db.query(Permission).all()
for p in perms:
    print(f"Permission: {p.code} (ID: {p.id}) - {p.description}")

print("\n--- USERS ---")
users = db.query(User).all()
for u in users:
    roles = [r.name for r in u.roles]
    print(f"User: {u.username} (ID: {u.id}) - Roles: {roles}")

db.close()
