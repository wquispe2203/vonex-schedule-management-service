from app.core.database import SessionLocal
from app.models import Teacher, Lesson, ScheduleSession, Observation, XmlUpload
from sqlalchemy import func

db = SessionLocal()
try:
    teachers = db.query(Teacher).all()
    print(f"Total teachers in DB: {len(teachers)}")
    
    active_count = 0
    incomplete_count = 0
    
    for t in teachers:
        # Check active relationships
        lessons_count = db.query(Lesson).filter(Lesson.teacher_id == t.id).count()
        
        # Correctly join ScheduleSession and Lesson to count sessions for this teacher
        sessions_count = db.query(ScheduleSession).join(
            Lesson, ScheduleSession.lesson_id == Lesson.id
        ).filter(Lesson.teacher_id == t.id).count()
        
        observations_as_teacher = db.query(Observation).filter(Observation.teacher_id == t.id).count()
        observations_as_replacement = db.query(Observation).filter(Observation.replacement_teacher_id == t.id).count()
        
        print(f"Teacher: {t.last_name}, {t.first_name}")
        print(f"  - ID: {t.id}")
        print(f"  - Source ID: {t.source_id}")
        print(f"  - Source: {t.source}")
        print(f"  - Status: {t.status}")
        print(f"  - DNI: {t.dni}")
        print(f"  - Merged Into: {t.merged_into_id}")
        print(f"  - Lessons count: {lessons_count}")
        print(f"  - ScheduleSessions count: {sessions_count}")
        print(f"  - Observations (Titular): {observations_as_teacher}")
        print(f"  - Observations (Replacement): {observations_as_replacement}")
        print("-" * 50)
        
        if t.status == "ACTIVO":
            active_count += 1
        elif t.status == "INCOMPLETO":
            incomplete_count += 1
            
    print(f"\nSummary:")
    print(f"ACTIVO: {active_count}")
    print(f"INCOMPLETO: {incomplete_count}")
    
    # Check total counts of XML uploads, sessions, lessons
    print(f"Total XmlUploads: {db.query(XmlUpload).count()}")
    print(f"Total ScheduleSessions: {db.query(ScheduleSession).count()}")
    print(f"Total Lessons: {db.query(Lesson).count()}")
    print(f"Total Observations: {db.query(Observation).count()}")
    
finally:
    db.close()
