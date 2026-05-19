from app.core.database import SessionLocal
from app.models.teacher import Teacher

db = SessionLocal()
try:
    print("TEACHER DETAILS:")
    teachers = db.query(Teacher).all()
    for t in teachers:
        print(f"ID: {t.id} | Name: {t.last_name}, {t.first_name} | SourceID: {t.source_id} | Source: {t.source} | Status: {t.status} | DNI: {t.dni}")
finally:
    db.close()
