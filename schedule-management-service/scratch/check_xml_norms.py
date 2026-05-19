from app.core.database import SessionLocal
from app.models import Teacher, XmlUpload
from app.modules.docentes.service import get_latest_completed_upload, get_docente_names_from_xml, normalize_name
import os

def run():
    db = SessionLocal()
    try:
        # Get the historical upload
        upload = db.query(XmlUpload).filter(XmlUpload.id == '8bc2c3a5-fa43-4cb2-8971-ebd07ccb5b84').first()
        print(f"Upload: {upload.filename}")
        
        xml_names = get_docente_names_from_xml(upload)
        xml_norms = {normalize_name(name) for name in xml_names if name}
        print(f"Total xml names: {len(xml_names)}")
        print(f"Total xml norms: {len(xml_norms)}")
        
        # Check the 4 incomplete teachers
        incompletes = db.query(Teacher).filter(Teacher.status == "INCOMPLETO").all()
        print(f"\nIncomplete Teachers: {len(incompletes)}")
        for t in incompletes:
            t_norm = normalize_name(f"{t.last_name} {t.first_name}")
            in_xml = t_norm in xml_norms
            print(f"Teacher: '{t.last_name}, {t.first_name}'")
            print(f"  - Normalized: '{t_norm}'")
            print(f"  - In XML norms: {in_xml}")
            
    finally:
        db.close()

if __name__ == "__main__":
    run()
