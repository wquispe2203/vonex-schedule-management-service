import json
from collections import defaultdict
from fastapi.testclient import TestClient
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models import Teacher, XmlUpload, User
from app.main import create_app
from app.modules.docentes.service import get_latest_completed_upload, get_docente_names_from_xml, _run_crossing_engine
import os

app = create_app()
client = TestClient(app)

def run():
    db = SessionLocal()
    output = {}
    try:
        # FASE A: Teacher Inventory
        total_teachers = db.query(Teacher).count()
        with_dni = db.query(Teacher).filter(Teacher.dni.isnot(None), Teacher.dni != '').count()
        without_dni = total_teachers - with_dni
        activo = db.query(Teacher).filter(Teacher.status == 'ACTIVO').count()
        incompleto = db.query(Teacher).filter(Teacher.status == 'INCOMPLETO').count()
        
        # Duplicates by normalized_name
        all_t = db.query(Teacher).all()
        by_norm = defaultdict(list)
        by_dni = defaultdict(list)
        by_source = defaultdict(list)
        
        for t in all_t:
            if t.normalized_name:
                by_norm[t.normalized_name].append(t)
            if t.dni and t.dni.strip():
                by_dni[t.dni].append(t)
                
        dup_norm = {k: [t.id for t in v] for k,v in by_norm.items() if len(v) > 1}
        dup_dni = {k: [t.id for t in v] for k,v in by_dni.items() if len(v) > 1}
        
        # FASE B: RPT Dropdown
        upload = get_latest_completed_upload(db)
        upload_info = {
            "id": str(upload.id) if upload else None,
            "filename": upload.filename if upload else None,
            "storage_path": upload.storage_path if upload else None,
            "exists": os.path.exists(upload.storage_path) if upload and upload.storage_path else False
        }
        extracted_names = get_docente_names_from_xml(upload) if upload else []
        
        # TestClient to endpoint
        # Need to authenticate or bypass auth.
        from app.dependencies.auth import get_current_active_user
        
        # Fetch a real admin user
        real_user = db.query(User).first()
        app.dependency_overrides[get_current_active_user] = lambda: real_user
        
        resp = client.get("/api/rpt-planilla/docentes", headers={"Authorization": "Bearer dummy"})
        dropdown_resp = {"status": resp.status_code, "json": resp.json() if resp.status_code == 200 else None}
        
        # FASE C: SIN ASIGNAR Crossing Engine
        cross_res = _run_crossing_engine(db)
        
        output = {
            "fase_a": {
                "total": total_teachers,
                "with_dni": with_dni,
                "without_dni": without_dni,
                "activo": activo,
                "incompleto": incompleto,
                "duplicates_norm": len(dup_norm),
                "duplicates_dni": len(dup_dni)
            },
            "fase_b": {
                "upload": upload_info,
                "extracted_count": len(extracted_names),
                "api_response_status": dropdown_resp["status"],
                "api_payload_size": len(dropdown_resp["json"]["data"]["data"]) if dropdown_resp["json"] and "data" in dropdown_resp["json"] else "N/A"
            },
            "fase_c": {
                "matched": len(cross_res.get("matched", [])),
                "sin_asignar": len(cross_res.get("sin_asignar", [])),
                "conflictos": len(cross_res.get("conflictos", []))
            }
        }
        
        with open("scratch/audit_phases_results.json", "w") as f:
            json.dump(output, f, indent=2)
            
    finally:
        db.close()

if __name__ == "__main__":
    run()
