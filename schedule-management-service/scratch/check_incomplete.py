from app.core.database import SessionLocal
from app.models import Teacher
from app.modules.docentes.service import get_latest_completed_upload, get_docente_names_from_xml, normalize_name

db = SessionLocal()
try:
    upload = get_latest_completed_upload(db)
    xml_names = get_docente_names_from_xml(upload) if upload else []
    xml_norms = {normalize_name(name) for name in xml_names if name}
    
    db_incompletes = db.query(Teacher).filter(
        Teacher.status == "INCOMPLETO",
        Teacher.merged_into_id.is_(None)
    ).all()
    
    print(f"Total incomplete teachers in DB: {len(db_incompletes)}")
    for t in db_incompletes:
        t_norm = normalize_name(f"{t.last_name} {t.first_name}")
        in_xml = t_norm in xml_norms
        print(f"Teacher: {t.last_name}, {t.first_name} | status: {t.status} | DNI: {t.dni} | In XML: {in_xml}")
finally:
    db.close()
