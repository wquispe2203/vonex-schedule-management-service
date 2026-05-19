from app.core.database import SessionLocal
from app.models.teacher import Teacher
from sqlalchemy import distinct

db = SessionLocal()
try:
    print("DISTINCT RAZON SOCIAL VALUES:")
    results = db.query(distinct(Teacher.razon_social)).all()
    for r in results:
        print(f"Value: {repr(r[0])}")
finally:
    db.close()
