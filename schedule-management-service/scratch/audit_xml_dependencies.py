from app.core.database import SessionLocal
from sqlalchemy import text
import os

db = SessionLocal()
try:
    print("=== XML HISTORICAL DEPENDENCY AUDIT ===")
    
    xml_id = "8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84"
    
    # 1. Get XML info
    xml_info = db.execute(text("SELECT id, filename, storage_path, status FROM xml_uploads WHERE id = :id"), {"id": xml_id}).fetchone()
    if xml_info:
        print(f"XML Upload: ID={xml_info[0]} | Filename={xml_info[1]} | StoragePath={xml_info[2]} | Status={xml_info[3]}")
        if xml_info[2]:
            exists = os.path.exists(xml_info[2])
            print(f"Physical file exists in storage: {exists} ({xml_info[2]})")
    else:
        print(f"XML with ID {xml_id} NOT found!")
        
    # 2. Schedule sessions count
    sessions_count = db.execute(text("SELECT COUNT(*) FROM schedule_sessions WHERE xml_upload_id = :id"), {"id": xml_id}).scalar()
    print(f"Schedule Sessions count: {sessions_count}")
    
    # 3. Rpt Planilla count
    rpt_count = db.execute(text("SELECT COUNT(*) FROM rpt_planilla WHERE xml_upload_id = :id"), {"id": xml_id}).scalar()
    print(f"Rpt Planilla count: {rpt_count}")
    
    # 4. Teacher Name Overrides count
    overrides_count = db.execute(text("SELECT COUNT(*) FROM teacher_name_overrides WHERE xml_upload_id = :id"), {"id": xml_id}).scalar()
    print(f"Teacher Name Overrides count: {overrides_count}")
    
    # 5. Observations related to sessions from this XML upload
    obs_count = db.execute(text("""
        SELECT COUNT(*) 
        FROM observations o 
        JOIN schedule_sessions s ON o.session_id = s.id 
        WHERE s.xml_upload_id = :id
    """), {"id": xml_id}).scalar()
    print(f"Observations linked via Schedule Sessions: {obs_count}")
    
    # 6. Lessons count associated (indirectly via sessions)
    lessons_count = db.execute(text("""
        SELECT COUNT(DISTINCT lesson_id) 
        FROM schedule_sessions 
        WHERE xml_upload_id = :id
    """), {"id": xml_id}).scalar()
    print(f"Distinct Lessons associated via Schedule Sessions: {lessons_count}")
    
    # Let's count how many total lessons are in the system, and how many are orphan or belong to this XML
    total_lessons = db.execute(text("SELECT COUNT(*) FROM lessons")).scalar()
    print(f"Total Lessons in system: {total_lessons}")
    
    # Let's check how many lessons are associated with schedule sessions from other XMLs (there are no other XMLs since total is 1)
    
finally:
    db.close()
