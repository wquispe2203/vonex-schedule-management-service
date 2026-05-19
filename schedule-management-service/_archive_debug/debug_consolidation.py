import sys
from app.core.database import SessionLocal
from app.modules.horarios import service
from app.models import Teacher
from sqlalchemy import or_

db = SessionLocal()
try:
    # Find teacher Ronald Vilchez
    t = db.query(Teacher).filter(or_(
        Teacher.first_name.ilike('%Ronald%'),
        Teacher.last_name.ilike('%Vilchez%')
    )).first()
    
    if not t:
        print("Target teacher 'Ronald Vilchez' not found, testing with a sample teacher instead.")
        t = db.query(Teacher).first()

    if t:
        print(f"Found teacher: {t.first_name} {t.last_name} ID: {t.id}")
        # Find an active range from debug script earlier 2026-03-02
        s_date = '2026-03-02'
        e_date = '2026-03-08'
        
        print(f"\n--- EXECUTING get_teacher_schedule_grid ---")
        grid = service.get_teacher_schedule_grid(db, t.id, s_date, e_date)
        
        print(f"\nFinal Results: {len(grid)} consolidated items returned.")
        
        # Analyze output
        for idx, row in enumerate(grid):
            print(f"ITEM {idx+1}: {row['date']} | {row['start_time']} -> {row['end_time']} | Course: {row['subject']} | Hrs: {row['horas_dictadas']}")
    else:
        print("No teachers found in DB to test.")

finally:
    db.close()
