import sys
import json
from app.core.database import SessionLocal
from app.models import Teacher

def run():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).filter(Teacher.dni.is_(None)).all()
        for t in teachers:
            print({
                "id": str(t.id),
                "first_name": t.first_name,
                "last_name": t.last_name,
                "status": t.status,
                "is_active": t.is_active,
                "is_assigned": t.is_assigned,
                "source": t.source
            })
    finally:
        db.close()

if __name__ == "__main__":
    run()
