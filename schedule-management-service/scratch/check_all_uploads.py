from app.core.database import SessionLocal
from app.models import XmlUpload

def run():
    db = SessionLocal()
    try:
        uploads = db.query(XmlUpload).order_by(XmlUpload.created_at.desc()).all()
        print(f"Total XML Uploads in DB: {len(uploads)}")
        for u in uploads:
            print(f"ID: {u.id}, Filename: {u.filename}, Status: {u.status}, Storage Path: {u.storage_path}, Created At: {u.created_at}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
