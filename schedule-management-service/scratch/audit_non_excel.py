from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- 31 Non-Excel Teachers in DB ---")
    teachers = db.execute(text("SELECT id, source_id, last_name, first_name, status, dni FROM teachers WHERE source_id NOT LIKE 'EXCEL_%' OR source_id IS NULL")).fetchall()
    for t in teachers:
        print(f"ID: {t[0]} | SourceId: {t[1]} | Name: {t[2]} {t[3]} | Status: {t[4]} | DNI: {t[5]}")
finally:
    db.close()
