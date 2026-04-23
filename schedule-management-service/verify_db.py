from app.database import SessionLocal
from app.models import Subject, Teacher, ClassGroup, Lesson, ScheduleSession, XmlUploadLog

db = SessionLocal()
print("Subjects:", db.query(Subject).count())
print("Teachers:", db.query(Teacher).count())
print("Classes:", db.query(ClassGroup).count())
print("Lessons:", db.query(Lesson).count())
print("ScheduleSessions:", db.query(ScheduleSession).count())
print("Logs:", db.query(XmlUploadLog).count())
db.close()
