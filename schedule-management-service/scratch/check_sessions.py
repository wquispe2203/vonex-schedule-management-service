from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print("--- COUNT OF schedule_sessions BY xml_upload_id ---")
    dist_sess = db.execute(text("SELECT xml_upload_id, COUNT(*) FROM schedule_sessions GROUP BY xml_upload_id;")).fetchall()
    for d in dist_sess:
        print(d)
        
    print("\n--- COUNT OF rpt_planilla BY xml_upload_id ---")
    dist_rpt = db.execute(text("SELECT xml_upload_id, COUNT(*) FROM rpt_planilla GROUP BY xml_upload_id;")).fetchall()
    for d in dist_rpt:
        print(d)
finally:
    db.close()
