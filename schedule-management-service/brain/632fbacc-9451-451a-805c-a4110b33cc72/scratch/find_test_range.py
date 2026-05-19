from app.core.database import SessionLocal
from app.models import XmlUpload, RptPlanilla
from sqlalchemy import func

db = SessionLocal()
uploads = db.query(XmlUpload).filter(XmlUpload.status == 'COMPLETED').all()
print(f"{'Upload ID':<40} | {'Start':<10} | {'End':<10} | {'Count'}")
print("-" * 75)
for u in uploads:
    count = db.query(RptPlanilla).filter(RptPlanilla.xml_upload_id == u.id).count()
    print(f"{str(u.id):<40} | {str(u.start_date):<10} | {str(u.end_date):<10} | {count}")
