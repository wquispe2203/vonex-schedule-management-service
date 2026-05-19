from app.core.database import SessionLocal
from app.modules.docentes.service import get_latest_completed_upload, get_docente_names_from_xml

def run():
    db = SessionLocal()
    try:
        latest = get_latest_completed_upload(db)
        if not latest:
            print("No completed uploads found!")
            return
            
        print(f"Latest upload ID: {latest.id}")
        print(f"Status: {latest.status}")
        print(f"File name: {latest.filename}")
        print(f"Storage path: {latest.storage_path}")
        
        import os
        if latest.storage_path and os.path.exists(latest.storage_path):
            print("Storage path EXISTS.")
            names = get_docente_names_from_xml(latest)
            print(f"Names extracted from XML: {len(names)}")
            if names:
                print(f"Sample names: {names[:5]}")
        else:
            print("Storage path DOES NOT EXIST or is None.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
