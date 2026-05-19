from app.core.database import SessionLocal
from app.models import XmlUpload

def run():
    db = SessionLocal()
    try:
        invalid_upload = db.query(XmlUpload).filter(XmlUpload.id == "a8ae6d95-b897-4207-8d40-d0caff90c5a0").first()
        if invalid_upload:
            print("Found invalid upload! Deleting it...")
            db.delete(invalid_upload)
            db.commit()
            print("Successfully deleted invalid upload.")
        else:
            print("Invalid upload not found.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
