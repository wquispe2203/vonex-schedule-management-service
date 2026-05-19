import os
from app.core.database import SessionLocal
from app.models import XmlUpload

def run():
    db = SessionLocal()
    try:
        uploads = db.query(XmlUpload).all()
        for u in uploads:
            print({
                "id": str(u.id),
                "filename": u.filename,
                "status": u.status,
                "storage_path": u.storage_path,
                "exists": os.path.exists(u.storage_path) if u.storage_path else False
            })
    finally:
        db.close()

if __name__ == "__main__":
    run()
