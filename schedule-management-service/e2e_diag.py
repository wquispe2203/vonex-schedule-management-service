import sys
import requests
import json
import time
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models import User

# --- SETUP AUTH ---
db = SessionLocal()
# Buscamos un usuario que tenga permisos de admin/subir_xml
# El repo usa UUID para el ID del usuario en el token
user = db.query(User).filter(User.is_active == True).first()
if not user:
    print("No active user found!")
    sys.exit(1)

print(f"Basing auth on user: {user.username} (ID: {user.id})")

# SEGUN app/dependencies/auth.py:
# user_id_str: str = payload.get("sub")
# user_id = UUID(user_id_str)
access_token = create_access_token(subject=str(user.id))
headers = {
    "Authorization": f"Bearer {access_token}"
}

print("=== FASE 1: VALIDACION DE DATOS REALES (CRITICO) ===")
xml_uploads = db.execute(text('SELECT id, filename, start_date, end_date FROM xml_uploads ORDER BY created_at DESC LIMIT 3')).fetchall()
print("XML Uploads (Ultimos 3):", xml_uploads)
print("Count schedule_sessions:", db.execute(text('SELECT COUNT(*) FROM schedule_sessions')).scalar())
print("Count rpt_planilla:", db.execute(text('SELECT COUNT(*) FROM rpt_planilla')).scalar())
print("Count teachers:", db.execute(text('SELECT COUNT(*) FROM teachers')).scalar())

print("\n=== FASE 2: VALIDACION DE ENDPOINTS REALES ===")
BASE_URL = "http://localhost:8000"

print(">> GET /api/schedule/xml-uploads")
r_xml = requests.get(f"{BASE_URL}/api/schedule/xml-uploads", headers=headers)
print("Status:", r_xml.status_code)
if r_xml.status_code != 200:
    print("Error Detail:", r_xml.text)
else:
    print("JSON Preview:", str(r_xml.json())[:300])

print("\n>> GET /api/rpt-planilla/?fecha_inicio=2026-03-02&fecha_fin=2026-03-08")
r_rpt = requests.get(f"{BASE_URL}/api/rpt-planilla/?fecha_inicio=2026-03-02&fecha_fin=2026-03-08", headers=headers)
print("Status:", r_rpt.status_code)
if r_rpt.status_code == 200:
    data_rpt = r_rpt.json()
    print("RPT Planilla items returned:", len(data_rpt.get("data", [])))
else:
    print("Error Detail:", r_rpt.text)

print("\n>> GET /api/rpt-planilla/docentes")
r_doc = requests.get(f"{BASE_URL}/api/rpt-planilla/docentes", headers=headers)
print("Status:", r_doc.status_code)
if r_doc.status_code == 200:
    data_doc = r_doc.json()
    print("Docentes items returned:", len(data_doc.get("data", [])))
else:
    print("Error Detail:", r_doc.text)

print("\n=== FASE 4 & 5: VALIDACION DE FLUJO XML COMPLETO & CRUCE DOCENTES ===")
xml_path = "test_mdm.xml"
print(f">> POST /api/schedule/upload with {xml_path}")
with open(xml_path, "rb") as f:
    files = {"file": (xml_path, f, "application/xml")}
    # El router espera start_date y end_date como Form
    data = {"start_date": "2026-03-09", "end_date": "2026-03-15", "force_overwrite": "true"}
    r_upload = requests.post(f"{BASE_URL}/api/schedule/upload", headers=headers, files=files, data=data)

print("Status:", r_upload.status_code)
if r_upload.status_code != 200:
    print("Upload Error Detail:", r_upload.text)
else:
    resp_upload = r_upload.json()
    print("Response:", resp_upload)

    time.sleep(1) # wait a moment for DB commit

    print("\n>> GET /api/schedule/xml-uploads/{upload_id}/report")
    upload_id = resp_upload.get("data", {}).get("upload_id") if isinstance(resp_upload.get("data"), dict) else resp_upload.get("upload_id")
    if upload_id:
        r_report = requests.get(f"{BASE_URL}/api/schedule/xml-uploads/{upload_id}/report", headers=headers)
        print("Status:", r_report.status_code)
        try:
            report_data = r_report.json()
            print("JSON Report keys:", report_data.get("data", {}).keys() if report_data.get("data") else "No data")
            print("Matched Exact:", len(report_data.get("data", {}).get("matched_exact", [])) if report_data.get("data") else 0)
            print("Matched Fuzzy:", len(report_data.get("data", {}).get("matched_fuzzy", [])) if report_data.get("data") else 0)
            print("Unmatched New:", len(report_data.get("data", {}).get("unmatched_new", [])) if report_data.get("data") else 0)
        except Exception as e:
            print("Error parsing report:", e)
    else:
        print("No upload_id returned from upload")

db.close()
