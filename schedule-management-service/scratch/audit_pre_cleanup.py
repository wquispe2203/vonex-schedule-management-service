import json
from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    inventory = {}
    
    # 1. Teachers
    inventory["teachers"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM teachers")).scalar(),
        "active": db.execute(text("SELECT COUNT(*) FROM teachers WHERE status = 'ACTIVO'")).scalar(),
        "incomplete": db.execute(text("SELECT COUNT(*) FROM teachers WHERE status = 'INCOMPLETO'")).scalar(),
        "excel_imported": db.execute(text("SELECT COUNT(*) FROM teachers WHERE source_id LIKE 'EXCEL_%'")).scalar(),
        "non_excel_active": db.execute(text("SELECT COUNT(*) FROM teachers WHERE (source_id NOT LIKE 'EXCEL_%' OR source_id IS NULL) AND status = 'ACTIVO'")).scalar(),
        "non_excel_incomplete": db.execute(text("SELECT COUNT(*) FROM teachers WHERE (source_id NOT LIKE 'EXCEL_%' OR source_id IS NULL) AND status = 'INCOMPLETO'")).scalar()
    }
    
    # 2. XmlUploads
    inventory["xml_uploads"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM xml_uploads")).scalar(),
        "names": db.execute(text("SELECT id, filename, status, created_at FROM xml_uploads")).fetchall()
    }
    # Convert tuples to list of dicts for JSON serialization
    inventory["xml_uploads"]["names"] = [
        {"id": str(r[0]), "filename": r[1], "status": r[2], "created_at": str(r[3])}
        for r in inventory["xml_uploads"]["names"]
    ]
    
    # 3. Schedule Sessions
    inventory["schedule_sessions"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM schedule_sessions")).scalar(),
        "by_xml_upload": db.execute(text("SELECT xml_upload_id, COUNT(*) FROM schedule_sessions GROUP BY xml_upload_id")).fetchall()
    }
    inventory["schedule_sessions"]["by_xml_upload"] = [
        {"xml_upload_id": str(r[0]), "count": r[1]}
        for r in inventory["schedule_sessions"]["by_xml_upload"]
    ]
    
    # 4. Rpt Planilla
    inventory["rpt_planilla"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM rpt_planilla")).scalar(),
        "by_xml_upload": db.execute(text("SELECT xml_upload_id, COUNT(*) FROM rpt_planilla GROUP BY xml_upload_id")).fetchall()
    }
    inventory["rpt_planilla"]["by_xml_upload"] = [
        {"xml_upload_id": str(r[0]), "count": r[1]}
        for r in inventory["rpt_planilla"]["by_xml_upload"]
    ]
    
    # 5. Observations
    inventory["observations"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM observations")).scalar(),
    }
    
    # 6. Lessons
    inventory["lessons"] = {
        "total": db.execute(text("SELECT COUNT(*) FROM lessons")).scalar(),
    }
    
    print(json.dumps(inventory, indent=2))
finally:
    db.close()
