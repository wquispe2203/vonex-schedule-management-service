from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Teacher, Subject, User, Grade
import uuid

def final_architectural_validation():
    db = SessionLocal()
    try:
        print("--- FINAL ARCHITECTURAL VALIDATION (SENIOR) ---")
        
        # 1. Master Table Check (Subjects) - Should only have ID as UUID
        subject = db.query(Subject).first()
        if subject:
            print(f"Subject: {subject.name}")
            print(f"  ID: {subject.id} (Type: {type(subject.id)})")
            # En el modelo ya no existe legacy_id para Subject
            try:
                print(f"  Legacy ID: {getattr(subject, 'legacy_id', 'NOT FOUND')}")
            except Exception:
                print("  Legacy ID: (Removed as expected)")
            assert isinstance(subject.id, uuid.UUID)

        # 2. Transactional Table Check (Teachers) - Should have ID (UUID) + legacy_id (Int)
        teacher = db.query(Teacher).first()
        if teacher:
            print(f"Teacher: {teacher.first_name} {teacher.last_name}")
            print(f"  ID: {teacher.id} (Type: {type(teacher.id)})")
            print(f"  Legacy ID: {teacher.legacy_id} (Type: {type(teacher.legacy_id)})")
            assert isinstance(teacher.id, uuid.UUID)
            assert isinstance(teacher.legacy_id, int)

        # 3. Relationship Check (Grade -> Class)
        grade = db.query(Grade).first()
        if grade:
            print(f"Grade: {grade.name}")
            print(f"  Classes associated: {len(grade.classes)}")
            for c in grade.classes:
                print(f"    Class: {c.name} (ID: {c.id})")

        print("\n[VERIFIED] Arquitectura Soberana UUID consolidada exitosamente.")
        
    except Exception as e:
        print(f"\n[ERROR] Fallo en la validación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    final_architectural_validation()
