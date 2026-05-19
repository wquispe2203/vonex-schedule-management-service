from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    count = db.execute(text("""
        SELECT COUNT(*) 
        FROM lessons 
        WHERE teacher_id IN (SELECT id FROM teachers WHERE source_id LIKE 'EXCEL_%')
    """)).scalar()
    print(f"Lessons associated with Excel teachers: {count}")
    
    # Also check if there are any sessions associated with those lessons
    sessions_count = db.execute(text("""
        SELECT COUNT(*) 
        FROM schedule_sessions 
        WHERE lesson_id IN (
            SELECT id FROM lessons WHERE teacher_id IN (SELECT id FROM teachers WHERE source_id LIKE 'EXCEL_%')
        )
    """)).scalar()
    print(f"Schedule sessions associated with Excel teachers: {sessions_count}")
    
finally:
    db.close()
