import sys
from uuid import UUID
from app.core.database import SessionLocal
from app.modules.horarios import service

db = SessionLocal()
try:
    class_id = UUID('7071b54c-66ac-4a93-9817-5d1a6d680a3a')
    s_date = '2026-03-09'
    e_date = '2026-03-15'
    print(f"Testing specific class: {class_id} in range {s_date} -> {e_date}")
    class_grid = service.get_classroom_schedule_grid(db, class_id, s_date, e_date)
    print(f"Classroom grid returns {len(class_grid)} rows.")
    if class_grid:
        print("SAMPLE CLASS SESSION:", class_grid[0])
finally:
    db.close()
