from app.core.database import SessionLocal
from app.models import Teacher

def run():
    db = SessionLocal()
    try:
        teachers = db.query(Teacher).all()
        print(f"Total teachers: {len(teachers)}")
        
        null_dni_teachers = [t for t in teachers if not t.dni]
        print(f"Teachers with null DNI: {len(null_dni_teachers)}")
        for t in null_dni_teachers:
            print({
                "id": str(t.id),
                "first_name": t.first_name,
                "last_name": t.last_name,
                "dni": t.dni,
                "status": t.status,
                "is_active": t.is_active
            })
    finally:
        db.close()

if __name__ == "__main__":
    run()
