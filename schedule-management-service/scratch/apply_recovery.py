import os
import shutil
import logging
from app.core.database import SessionLocal
from app.models import Teacher, XmlUpload
from app.services.xml_parser import XMLParserService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("apply_recovery")

def run():
    print("=== SURGICAL DATABASE RECOVERY AND AUDIT ===")
    
    # Define paths
    src_xml = "d:\\Desktop\\MOD HOR\\horario-academia-lima.xml"
    dest_dir = "d:\\Desktop\\MOD HOR\\schedule-management-service\\storage\\xml_uploads"
    dest_xml = os.path.join(dest_dir, "historical_xml_import_202603.xml")
    db_relative_path = "storage/xml_uploads/historical_xml_import_202603.xml"
    
    # 1. Physical XML Asset Relink check
    if not os.path.exists(src_xml):
        print(f"[FATAL] Source XML file not found at: {src_xml}")
        return
        
    print(f"[ASSET] Found original academic schedule XML file at: {src_xml}")
    
    if not os.path.exists(dest_dir):
        print(f"[ASSET] Target directory {dest_dir} does not exist. Creating it...")
        os.makedirs(dest_dir, exist_ok=True)
        
    # Copy file physically
    try:
        shutil.copy2(src_xml, dest_xml)
        print(f"[ASSET SUCCESS] Copied XML to: {dest_xml}")
    except Exception as e:
        print(f"[FATAL] Failed to copy XML file: {e}")
        return
        
    db = SessionLocal()
    try:
        # Start Transaction
        print("[TX START] Beginning secure database transaction...")
        
        # A. Snapshot BEFORE changes
        print("\n--- BEFORE SNAPSHOT ---")
        
        # 1. XML upload target
        target_upload = db.query(XmlUpload).filter(XmlUpload.id == '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84').first()
        if target_upload:
            print(f"[BEFORE XmlUpload] ID: {target_upload.id}, Filename: {target_upload.filename}, Storage Path: {target_upload.storage_path}, Status: {target_upload.status}")
        else:
            print("[BEFORE XmlUpload] Target XML upload not found!")
            
        # 2. Null DNI active teachers
        null_dni_active = db.query(Teacher).filter(
            Teacher.status == "ACTIVO",
            (Teacher.dni.is_(None) | (Teacher.dni == ""))
        ).all()
        
        print(f"[BEFORE Teachers] Found {len(null_dni_active)} ACTIVO teachers with NULL or empty DNI:")
        for t in null_dni_active:
            print(f"  - ID: {t.id}, Name: {t.last_name}, {t.first_name}, DNI: {t.dni}, Status: {t.status}")
            
        # B. Perform updates
        print("\n[TX APPLY] Executing SQL mutations...")
        
        # 1. Update storage_path of virtual XML
        if target_upload:
            target_upload.storage_path = db_relative_path
            print(f"[TX UPDATE] Updated storage_path of XML upload '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84' to '{db_relative_path}'")
        else:
            raise Exception("Cannot update: historical_xml_import_202603.xml not found in DB!")
            
        # 2. Update status of those 4 null-DNI ACTIVO teachers to 'INCOMPLETO'
        updated_count = 0
        for t in null_dni_active:
            t.status = "INCOMPLETO"
            updated_count += 1
            
        print(f"[TX UPDATE] Set status to 'INCOMPLETO' for {updated_count} null-DNI teachers.")
        
        # Commit Transaction
        db.commit()
        print("[TX COMMIT] Database transaction committed successfully!")
        
        # C. Snapshot AFTER changes
        print("\n--- AFTER SNAPSHOT ---")
        
        # Refresh and print target upload
        db.refresh(target_upload)
        print(f"[AFTER XmlUpload] ID: {target_upload.id}, Filename: {target_upload.filename}, Storage Path: {target_upload.storage_path}, Status: {target_upload.status}")
        
        # Re-check for any null DNI active teachers
        remaining_null_dni_active = db.query(Teacher).filter(
            Teacher.status == "ACTIVO",
            (Teacher.dni.is_(None) | (Teacher.dni == ""))
        ).all()
        print(f"[AFTER Teachers] Remaining ACTIVO teachers with NULL or empty DNI: {len(remaining_null_dni_active)}")
        
        # Query updated teachers
        print("[AFTER Teachers] Updated teachers validation:")
        for t in null_dni_active:
            db.refresh(t)
            print(f"  - ID: {t.id}, Name: {t.last_name}, {t.first_name}, DNI: {t.dni}, Status: {t.status}")
            
    except Exception as ex:
        db.rollback()
        print(f"\n[TX ROLLBACK] Transaction rolled back due to error: {ex}")
    finally:
        db.close()
        print("\n=== RECOVERY AND AUDIT COMPLETE ===")

if __name__ == "__main__":
    run()
