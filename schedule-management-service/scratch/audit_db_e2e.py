import sys
import json
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models import Teacher, Lesson, ScheduleSession, XmlUpload, RptPlanilla, Observation

def run_audit():
    db = SessionLocal()
    try:
        report = {}
        
        # 1. Teachers
        report['teachers_total'] = db.query(Teacher).count()
        report['teachers_dni_null'] = db.query(Teacher).filter(Teacher.dni.is_(None)).count()
        report['teachers_dni_empty'] = db.query(Teacher).filter(Teacher.dni == "").count()
        report['teachers_status'] = dict(db.query(Teacher.status, func.count(Teacher.id)).group_by(Teacher.status).all())
        report['teachers_merged'] = db.query(Teacher).filter(Teacher.merged_into_id.isnot(None)).count()
        
        # 2. XmlUploads
        report['xml_uploads_total'] = db.query(XmlUpload).count()
        report['xml_uploads_status'] = dict(db.query(XmlUpload.status, func.count(XmlUpload.id)).group_by(XmlUpload.status).all())
        
        # 3. Sessions & Lessons
        report['lessons_total'] = db.query(Lesson).count()
        report['sessions_total'] = db.query(ScheduleSession).count()
        report['sessions_null_xml'] = db.query(ScheduleSession).filter(ScheduleSession.xml_upload_id.is_(None)).count()
        
        # 4. Rpt Planilla
        report['rpt_planilla_total'] = db.query(RptPlanilla).count()
        report['rpt_planilla_null_xml'] = db.query(RptPlanilla).filter(RptPlanilla.xml_upload_id.is_(None)).count()
        
        # 5. Observations
        report['observations_total'] = db.query(Observation).count()
        
        print(json.dumps(report, indent=2))
    finally:
        db.close()

if __name__ == "__main__":
    run_audit()
