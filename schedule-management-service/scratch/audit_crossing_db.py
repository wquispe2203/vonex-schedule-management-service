import os
import sys
import json
from pathlib import Path

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.database import SessionLocal
    from app.modules.docentes.service import (
        _run_crossing_engine,
        get_sinasignar_crossed,
        get_conflictos_crossed,
        get_latest_completed_upload
    )
    from app.models import Teacher, TeacherNameOverride
    
    db = SessionLocal()
    
    print("--- 1. XML & DATABASE STATE ---")
    latest = get_latest_completed_upload(db)
    print(f"Latest Completed Upload: {latest.filename if latest else 'None'}")
    if latest:
        print(f"  UUID: {latest.id}")
    
    total_teachers = db.query(Teacher).count()
    active_teachers = db.query(Teacher).filter(Teacher.merged_into_id.is_(None)).all()
    incomplete_teachers = db.query(Teacher).filter(Teacher.status == "INCOMPLETO", Teacher.merged_into_id.is_(None)).count()
    overrides_count = db.query(TeacherNameOverride).count()
    
    print(f"Total Teachers in DB: {total_teachers}")
    print(f"Active Teachers (Non-merged): {len(active_teachers)}")
    print(f"Incomplete Teachers (Sin Asignar): {incomplete_teachers}")
    print(f"Total Override Mappings registered: {overrides_count}")
    
    print("\n--- 2. RUNNING CROSSING ENGINE ---")
    crossing_results = _run_crossing_engine(db)
    print(f"Engine Results:")
    print(f"  Matched pairs: {len(crossing_results.get('matched', []))}")
    print(f"  Unassigned (Sin Asignar) count: {len(crossing_results.get('sin_asignar', []))}")
    print(f"  Conflicts (Conflictos) count: {len(crossing_results.get('conflictos', []))}")
    
    print("\n--- 3. TESTING ENDPOINTS (SERVICE LAYER) ---")
    sin_asignar_response = get_sinasignar_crossed(db, page=1, limit=50)
    conflictos_response = get_conflictos_crossed(db, page=1, limit=50)
    
    print(f"Sin Asignar Service Response: success={sin_asignar_response.success}, total={sin_asignar_response.data.total}")
    print(f"Conflictos Service Response: success={conflictos_response.success}, total={conflictos_response.data.total}")
    
    # Save audit metrics to JSON
    audit_data = {
        "latest_completed_upload": str(latest.id) if latest else None,
        "latest_filename": latest.filename if latest else None,
        "database_teachers": {
            "total": total_teachers,
            "active": len(active_teachers),
            "incomplete": incomplete_teachers,
            "overrides": overrides_count
        },
        "crossing_engine": {
            "matched": len(crossing_results.get("matched", [])),
            "sin_asignar": len(crossing_results.get("sin_asignar", [])),
            "conflictos": len(crossing_results.get("conflictos", []))
        },
        "service_layer": {
            "sin_asignar_total": sin_asignar_response.data.total,
            "conflictos_total": conflictos_response.data.total
        }
    }
    
    out_path = Path("d:/Desktop/MOD HOR/schedule-management-service/scratch/crossing_audit_results.json")
    out_path.write_text(json.dumps(audit_data, indent=2), encoding="utf-8")
    print(f"\nAudit results successfully saved to {out_path}")
    
except Exception as e:
    import traceback
    print(f"Error during crossing engine audit: {str(e)}")
    traceback.print_exc()
finally:
    db.close()
