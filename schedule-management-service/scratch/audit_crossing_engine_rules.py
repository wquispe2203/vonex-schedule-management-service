from app.core.database import SessionLocal
from app.models import Teacher, XmlUpload
from app.modules.docentes.service import get_sinasignar_crossed, get_active_teachers_for_rpt
import json

def run():
    print("=== CROSSING ENGINE & RPT DROPDOWN SIMULATION ===")
    db = SessionLocal()
    try:
        # A. Current state (broken due to temp_rule_test_upload.xml)
        print("\n--- CURRENT STATE (Using latest COMPLETED) ---")
        latest_db = db.query(XmlUpload).filter(XmlUpload.status == 'COMPLETED').order_by(XmlUpload.created_at.desc()).first()
        print(f"Latest Completed Upload in DB: ID={latest_db.id}, Filename='{latest_db.filename}', Storage Path={latest_db.storage_path}")
        
        sa_current = get_sinasignar_crossed(db)
        print(f"Current Sin Asignar Count: {sa_current.data.total}")
        
        rpt_current = get_active_teachers_for_rpt(db)
        print(f"Current RPT Dropdown Count: {len(rpt_current)}")
        
        # B. Robust Query State (Filtering uploads with null/missing storage path)
        print("\n--- ROBUST STATE (Filtering out NULL/missing storage paths) ---")
        
        # Let's find the latest completed upload that actually has a storage path and exists on disk
        import os
        robust_upload = None
        all_completed = db.query(XmlUpload).filter(XmlUpload.status == 'COMPLETED').order_by(XmlUpload.created_at.desc()).all()
        for u in all_completed:
            if u.storage_path and os.path.exists(u.storage_path):
                robust_upload = u
                break
                
        if robust_upload:
            print(f"Robust Latest Completed Upload: ID={robust_upload.id}, Filename='{robust_upload.filename}', Storage Path={robust_upload.storage_path}")
            
            # Let's mock get_latest_completed_upload to return our robust_upload!
            import app.modules.docentes.service as docentes_service
            original_func = docentes_service.get_latest_completed_upload
            docentes_service.get_latest_completed_upload = lambda db: robust_upload
            
            try:
                sa_robust = get_sinasignar_crossed(db)
                print(f"Robust Sin Asignar Count: {sa_robust.data.total}")
                if sa_robust.data.total > 0:
                    print("Sample unassigned teachers:")
                    for t in sa_robust.data.data[:5]:
                        print(f"  - {t['apellidos']}, {t['nombres']} (DNI: {t['dni']}, Source: {t['source']})")
                        
                rpt_robust = get_active_teachers_for_rpt(db)
                print(f"Robust RPT Dropdown Count: {len(rpt_robust)}")
                if len(rpt_robust) > 0:
                    print("Sample RPT dropdown teachers:")
                    for t in rpt_robust[:5]:
                        print(f"  - {t['name']} (DNI: {t['dni']}, XML Hours: {t['total_hours']})")
            finally:
                docentes_service.get_latest_completed_upload = original_func
        else:
            print("No completed upload with valid physical file exists in the database!")
            
    finally:
        db.close()
        print("\n=== SIMULATION COMPLETE ===")

if __name__ == "__main__":
    run()
