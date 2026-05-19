from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()

indexes = [
    "CREATE INDEX IF NOT EXISTS idx_rpt_planilla_fecha_sede ON rpt_planilla (fecha_clase, sede)",
    "CREATE INDEX IF NOT EXISTS idx_schedule_sessions_date_upload ON schedule_sessions (session_date, xml_upload_id)",
    "CREATE INDEX IF NOT EXISTS idx_rpt_planilla_upload_id ON rpt_planilla (xml_upload_id)"
]

print("Applying performance indexes...")
for idx in indexes:
    try:
        db.execute(text(idx))
        db.commit()
        print(f"SUCCESS: {idx}")
    except Exception as e:
        db.rollback()
        print(f"FAILED: {idx} | Error: {e}")

print("Index application complete.")
