from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- XML Uploads ---")
    uploads = db.execute(text("SELECT id, filename, storage_path, status, created_at FROM xml_uploads")).fetchall()
    for u in uploads:
        print(u)
finally:
    db.close()
