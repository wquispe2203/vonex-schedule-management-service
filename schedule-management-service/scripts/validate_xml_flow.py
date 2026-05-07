import sys
import os
import shutil
from sqlalchemy.orm import Session
from uuid import UUID

# Add project path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.xml_upload import XMLUploadService
from app.models import User

def validate_xml_flow():
    db: Session = SessionLocal()
    service = XMLUploadService()
    
    # Use an existing user or create a dummy one for audit logs
    user = db.query(User).first()
    if not user:
        print("[SKIP] No users found in DB to perform test.")
        return

    xml_path = "storage/xml_uploads/complex_mdm_test_v2.xml"
    if not os.path.exists(xml_path):
        print(f"[ERROR] Sample XML not found: {xml_path}")
        return

    print(f"--- SIMULATING XML UPLOAD FLOW: {xml_path} ---")
    
    try:
        # We use a transaction that we will ROLLBACK at the end to avoid polluting the DB
        # However, XMLUploadService calls db.commit() inside. 
        # For a safer test, we'll use a temporary copy or just accept the test data.
        
        result = service.process_upload(
            db=db,
            file_path=xml_path,
            start_date="2026-04-21",
            end_date="2026-04-27",
            overwrite=True, # We use overwrite to avoid "duplicate range" error
            user_id=user.id,
            original_filename="validation_test.xml",
            usuario=user.username
        )
        
        if result.get("success"):
            print("[SUCCESS] XML Flow validated correctly.")
            print(f"  Records inserted: {result.get('records')}")
            # We don't rollback here because process_upload commits. 
            # In a real environment, we would use a separate test DB.
        else:
            print(f"[FAIL] XML Flow failed: {result.get('message')}")
            if result.get("conflicts"):
                print(f"  Conflicts: {result.get('conflicts')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"[CRITICAL] Runtime error during XML flow: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    validate_xml_flow()
