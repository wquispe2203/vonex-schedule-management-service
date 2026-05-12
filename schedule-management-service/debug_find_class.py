from app.core.database import SessionLocal
from app.models import ScheduleSession, Lesson, ClassGroup

db = SessionLocal()
try:
    # Find a session joined to a class
    s = db.query(ScheduleSession).join(Lesson).join(ClassGroup).first()
    if s:
        print(f"Class group with sessions: {s.lesson.class_group.name} ID: {s.lesson.class_group.id}")
        print(f"Date: {s.session_date}")
    else:
        print("No sessions found at all.")
finally:
    db.close()
