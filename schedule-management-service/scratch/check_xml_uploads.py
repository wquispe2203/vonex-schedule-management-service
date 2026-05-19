from app.core.database import SessionLocal
from app.models import XmlUpload

def run():
    db = SessionLocal()
    try:
        uploads = db.query(XmlUpload).order_by(XmlUpload.created_at.desc()).all()
        for u in uploads:
            print(f"ID: {u.id} | Status: {u.status} | File: {u.filename} | Path: {u.storage_path}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
