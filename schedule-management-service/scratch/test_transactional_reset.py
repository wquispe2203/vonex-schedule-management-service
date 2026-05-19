from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
transaction = db.begin()
try:
    print("Starting transactional reset test...")
    xml_id = "8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84"
    
    # 1. Observations
    deleted_obs = db.execute(text("DELETE FROM observations")).rowcount
    print(f"Deleted observations: {deleted_obs}")
    
    # 2. Rpt Planilla
    deleted_rpt = db.execute(text("DELETE FROM rpt_planilla WHERE xml_upload_id = :xml_id"), {"xml_id": xml_id}).rowcount
    print(f"Deleted rpt_planilla: {deleted_rpt}")
    
    # 3. Schedule Sessions
    deleted_sessions = db.execute(text("DELETE FROM schedule_sessions WHERE xml_upload_id = :xml_id"), {"xml_id": xml_id}).rowcount
    print(f"Deleted schedule_sessions: {deleted_sessions}")
    
    # 4. Lessons
    deleted_lessons = db.execute(text("DELETE FROM lessons WHERE id NOT IN (SELECT DISTINCT lesson_id FROM schedule_sessions)")).rowcount
    print(f"Deleted lessons: {deleted_lessons}")
    
    # 5. Excel Teachers
    deleted_teachers = db.execute(text("DELETE FROM teachers WHERE source_id LIKE 'EXCEL_%' AND source = 'manual'")).rowcount
    print(f"Deleted Excel teachers: {deleted_teachers}")
    
    # 6. Xml Uploads
    deleted_uploads = db.execute(text("DELETE FROM xml_uploads WHERE id = :xml_id"), {"xml_id": xml_id}).rowcount
    print(f"Deleted xml_uploads: {deleted_uploads}")
    
    # Verify remaining counts
    teachers_remaining = db.execute(text("SELECT COUNT(*) FROM teachers")).scalar()
    lessons_remaining = db.execute(text("SELECT COUNT(*) FROM lessons")).scalar()
    sessions_remaining = db.execute(text("SELECT COUNT(*) FROM schedule_sessions")).scalar()
    rpt_remaining = db.execute(text("SELECT COUNT(*) FROM rpt_planilla")).scalar()
    obs_remaining = db.execute(text("SELECT COUNT(*) FROM observations")).scalar()
    uploads_remaining = db.execute(text("SELECT COUNT(*) FROM xml_uploads")).scalar()
    
    print("\n--- Remaining Counts ---")
    print(f"Teachers remaining: {teachers_remaining} (Expected 31)")
    print(f"Lessons remaining: {lessons_remaining} (Expected 377)")
    print(f"Sessions remaining: {sessions_remaining} (Expected 0)")
    print(f"RptPlanilla remaining: {rpt_remaining} (Expected 0)")
    print(f"Observations remaining: {obs_remaining} (Expected 0)")
    print(f"XmlUploads remaining: {uploads_remaining} (Expected 0)")
    
    print("\nTransaction executed successfully without errors. Rolling back...")
    transaction.rollback()
    print("Rollback complete.")
except Exception as e:
    transaction.rollback()
    print(f"Error during transaction test: {e}")
finally:
    db.close()
