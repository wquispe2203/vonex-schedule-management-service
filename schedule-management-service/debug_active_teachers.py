from app.core.database import SessionLocal
from app.models import Teacher, Lesson, ScheduleSession, XmlUpload

db = SessionLocal()
try:
    total = db.query(Teacher).count()
    print(f"TOTAL Teachers in master: {total}")
    
    active_q = (
        db.query(Teacher.id)
        .join(Lesson, Teacher.id == Lesson.teacher_id)
        .join(ScheduleSession, Lesson.id == ScheduleSession.lesson_id)
        .join(XmlUpload, ScheduleSession.xml_upload_id == XmlUpload.id)
        .filter(XmlUpload.status == 'COMPLETED')
        .distinct()
    )
    active_count = active_q.count()
    print(f"ACTIVE Teachers (in COMPLETED uploads): {active_count}")
    
    # Check sample
    samples = active_q.limit(5).all()
    print("Sample Active IDs:", samples)

finally:
    db.close()
