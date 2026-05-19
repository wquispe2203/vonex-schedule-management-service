from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    for table in ["teachers", "subjects", "classes", "lessons", "schedule_sessions", "observations", "rpt_planilla"]:
        res = db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
        print(f"{table}: {res}")
finally:
    db.close()
