import sys
from uuid import UUID
from app.core.database import SessionLocal
from app.modules.horarios import repository, service
from app.models import Teacher, ClassGroup, XmlUpload

db = SessionLocal()
try:
    # Get first completed upload to pick reasonable dates
    u = db.query(XmlUpload).filter(XmlUpload.status == "COMPLETED").order_by(XmlUpload.created_at.desc()).first()
    if not u:
        print("NO COMPLETED UPLOADS FOUND")
        sys.exit(0)
        
    s_date = str(u.start_date)
    e_date = str(u.end_date)
    print(f"Found upload {u.id} for {s_date} -> {e_date}")

    # Test fetch_all_teachers
    teachers = repository.fetch_all_teachers(db)
    print(f"Total teachers: {len(teachers)}")

    # Test specific teacher grid for one of the teachers
    if teachers:
        t = teachers[0]
        print(f"Testing grid for teacher: {t.first_name} {t.last_name} ({t.id})")
        grid_data = service.get_teacher_schedule_grid(db, t.id, s_date, e_date)
        print(f"Grid returns {len(grid_data)} rows.")
        if grid_data:
            print("SAMPLE ROW:", grid_data[0])

    # Test fetch_all_classes
    classes = repository.fetch_all_classes(db)
    print(f"Total classes: {len(classes)}")
    if classes:
        c = classes[0]
        print(f"Testing grid for classroom: {c.name} ({c.id})")
        class_grid = service.get_classroom_schedule_grid(db, c.id, s_date, e_date)
        print(f"Classroom grid returns {len(class_grid)} rows.")

finally:
    db.close()
