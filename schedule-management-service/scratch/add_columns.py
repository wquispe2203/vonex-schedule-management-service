import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("Adding xml_upload_id to rpt_planilla...")
    db.execute(text("""
        ALTER TABLE rpt_planilla 
        ADD COLUMN IF NOT EXISTS xml_upload_id UUID REFERENCES xml_uploads(id) ON DELETE CASCADE;
    """))
    db.commit()
    print("Added successfully to rpt_planilla.")

    print("Adding xml_upload_id to schedule_sessions...")
    db.execute(text("""
        ALTER TABLE schedule_sessions 
        ADD COLUMN IF NOT EXISTS xml_upload_id UUID REFERENCES xml_uploads(id) ON DELETE CASCADE;
    """))
    db.commit()
    print("Added successfully to schedule_sessions.")

    # Let's populate existing rows with the correct xml_upload_id
    print("Associating existing rpt_planilla rows with completed uploads...")
    db.execute(text("""
        UPDATE rpt_planilla r
        SET xml_upload_id = u.id
        FROM xml_uploads u
        WHERE u.status = 'COMPLETED'
          AND r.fecha_clase >= u.start_date 
          AND r.fecha_clase <= u.end_date
          AND r.xml_upload_id IS NULL;
    """))
    db.commit()

    print("Associating existing schedule_sessions rows with completed uploads...")
    db.execute(text("""
        UPDATE schedule_sessions s
        SET xml_upload_id = u.id
        FROM xml_uploads u
        WHERE u.status = 'COMPLETED'
          AND s.session_date >= u.start_date 
          AND s.session_date <= u.end_date
          AND s.xml_upload_id IS NULL;
    """))
    db.commit()
    print("Existing rows successfully associated.")

    # Check remaining NULLs
    null_rpt = db.execute(text("SELECT COUNT(*) FROM rpt_planilla WHERE xml_upload_id IS NULL;")).fetchone()[0]
    null_sess = db.execute(text("SELECT COUNT(*) FROM schedule_sessions WHERE xml_upload_id IS NULL;")).fetchone()[0]
    print(f"Remaining NULLs in rpt_planilla: {null_rpt}")
    print(f"Remaining NULLs in schedule_sessions: {null_sess}")

    if null_rpt > 0 or null_sess > 0:
        # Fallback to the absolute latest completed upload for any remaining NULLs
        latest_id = db.execute(text("SELECT id FROM xml_uploads WHERE status = 'COMPLETED' ORDER BY created_at DESC LIMIT 1;")).fetchone()
        if latest_id:
            uid = latest_id[0]
            print(f"Applying absolute latest completed upload fallback: {uid}")
            db.execute(text("UPDATE rpt_planilla SET xml_upload_id = :uid WHERE xml_upload_id IS NULL;"), {"uid": uid})
            db.execute(text("UPDATE schedule_sessions SET xml_upload_id = :uid WHERE xml_upload_id IS NULL;"), {"uid": uid})
            db.commit()
            print("Remaining NULLs populated successfully.")

finally:
    db.close()
