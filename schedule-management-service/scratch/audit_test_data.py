import json
from app.core.database import SessionLocal
from app.models import XmlUpload, Teacher, Lesson, ScheduleSession, RptPlanilla, Observation

def run():
    db = SessionLocal()
    try:
        # 1. Identify Test/Recent Uploads
        # Historical ID to preserve: 8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84
        historical_xml_id = "8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84"
        
        all_uploads = db.query(XmlUpload).all()
        test_uploads = []
        for u in all_uploads:
            if str(u.id) != historical_xml_id:
                test_uploads.append({
                    "id": str(u.id),
                    "filename": u.filename,
                    "status": u.status,
                    "created_at": str(u.created_at)
                })
                
        # 2. Identify Test Teachers
        # E.g. named "TEST", "PRUEBA", or created recently.
        # Let's count how many teachers there are, and see if there are obvious test ones.
        all_teachers = db.query(Teacher).all()
        test_teachers = []
        for t in all_teachers:
            name = f"{t.last_name or ''} {t.first_name or ''}".upper()
            if "TEST" in name or "PRUEBA" in name or "DUMMY" in name or "MOCK" in name:
                test_teachers.append({
                    "id": str(t.id),
                    "name": name,
                    "status": t.status,
                    "created_at": str(t.created_at) if hasattr(t, 'created_at') and t.created_at else None
                })
                
        # 3. Identify records linked to test uploads
        test_upload_ids = [u['id'] for u in test_uploads]
        
        lessons_count = db.query(Lesson).filter(Lesson.xml_upload_id.in_(test_upload_ids)).count() if test_upload_ids else 0
        sessions_count = db.query(ScheduleSession).filter(ScheduleSession.xml_upload_id.in_(test_upload_ids)).count() if test_upload_ids else 0
        rpt_count = db.query(RptPlanilla).filter(RptPlanilla.xml_upload_id.in_(test_upload_ids)).count() if test_upload_ids else 0
        
        output = {
            "test_uploads": test_uploads,
            "test_teachers": test_teachers,
            "impact": {
                "lessons": lessons_count,
                "schedule_sessions": sessions_count,
                "rpt_planilla": rpt_count
            }
        }
        
        with open("scratch/audit_test_data_results.json", "w") as f:
            json.dump(output, f, indent=2)
            
        print("Audit completed. Results saved to scratch/audit_test_data_results.json")
        
    finally:
        db.close()

if __name__ == "__main__":
    run()
