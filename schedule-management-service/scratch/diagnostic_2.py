import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- 1. NULL COUNT IN rpt_planilla ---")
    null_rpt = db.execute(text("SELECT COUNT(*) FROM rpt_planilla WHERE xml_upload_id IS NULL;")).fetchone()[0]
    print(f"rpt_planilla with NULL xml_upload_id: {null_rpt}")

    print("\n--- 2. NULL COUNT IN schedule_sessions ---")
    null_sess = db.execute(text("SELECT COUNT(*) FROM schedule_sessions WHERE xml_upload_id IS NULL;")).fetchone()[0]
    print(f"schedule_sessions with NULL xml_upload_id: {null_sess}")

    print("\n--- 3. TOTAL COUNT IN rpt_planilla ---")
    total_rpt = db.execute(text("SELECT COUNT(*) FROM rpt_planilla;")).fetchone()[0]
    print(f"Total rpt_planilla records: {total_rpt}")

    print("\n--- 4. UPLOADS AND THEIR STATUS AND DATE RANGES ---")
    uploads = db.execute(text("SELECT id, filename, created_at, status, start_date, end_date FROM xml_uploads ORDER BY created_at DESC;")).fetchall()
    for u in uploads:
        print(u)

    print("\n--- 5. DISTRIBUTION OF rpt_planilla BY xml_upload_id ---")
    dist = db.execute(text("SELECT xml_upload_id, COUNT(*) FROM rpt_planilla GROUP BY xml_upload_id;")).fetchall()
    for d in dist:
        print(d)

    print("\n--- 6. SEARCH FOR 'Sannchez' AND 'Marya' IN DB ---")
    teachers = db.execute(text("SELECT id, last_name, first_name, status, source FROM teachers WHERE last_name ILIKE '%Sannchez%' OR first_name ILIKE '%Marya%' OR last_name ILIKE '%Marya%';")).fetchall()
    print("Found teachers:")
    for t in teachers:
        print(t)

finally:
    db.close()
