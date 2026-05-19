import os
from dotenv import load_dotenv
load_dotenv()
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    db.execute(text("ALTER TABLE roles ADD COLUMN is_protected BOOLEAN DEFAULT FALSE;"))
    db.commit()
    print("Column added successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
