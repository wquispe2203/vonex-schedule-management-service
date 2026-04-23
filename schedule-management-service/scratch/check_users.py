import sys
import os
from sqlalchemy import text
from sqlalchemy.orm import Session

# Ajustar el path para importar app
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"{'Username':<30} | {'ID (UUID)':<40} | {'Is Active':<10}")
        print("-" * 85)
        for u in users:
            print(f"{u.username:<30} | {str(u.id):<40} | {u.is_active:<10}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
