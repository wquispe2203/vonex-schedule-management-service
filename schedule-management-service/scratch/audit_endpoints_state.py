import sys
import os
import json
from uuid import UUID

# Ensure we can load app
sys.path.insert(0, os.path.abspath('.'))

from app.core.database import SessionLocal
from app.models import User, Role, Permission, Teacher, XmlUpload
from fastapi.testclient import TestClient
from app.main import app

def format_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False)

def run_audit():
    db = SessionLocal()
    client = TestClient(app)
    
    print("==================================================")
    print("1. ROLES AND PERMISSIONS AUDIT")
    print("==================================================")
    roles = db.query(Role).all()
    for role in roles:
        permissions = [p.code for p in role.permissions]
        print(f"Role: {role.name} | Permissions: {permissions}")
        
    print("\n==================================================")
    print("2. USERS AUDIT")
    print("==================================================")
    users = db.query(User).all()
    for user in users:
        print(f"User: {user.username} | Roles: {[r.name for r in user.roles]} | Active: {user.is_active}")

    # Let's check how many teachers and XML uploads exist
    teachers_count = db.query(Teacher).count()
    xml_completed_count = db.query(XmlUpload).filter(XmlUpload.status == "COMPLETED").count()
    xml_total_count = db.query(XmlUpload).count()
    print(f"\nTotal Teachers: {teachers_count}")
    print(f"Total XML Uploads (Any): {xml_total_count}")
    print(f"Total Completed XML Uploads: {xml_completed_count}")

    print("\n==================================================")
    print("3. DEV-LOGIN DIRECT ENDPOINT TEST")
    print("==================================================")
    # Let's test the dev-login response
    response = client.get("/api/users/dev-login")
    print(f"Status Code: {response.status_code}")
    print(f"Payload: {response.text}")
    
    # Extract the token if success
    token = None
    if response.status_code == 200:
        res_data = response.json()
        token = res_data.get("access_token")
        print("Successfully obtained dev-login token!")
        
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    print("\n==================================================")
    print("4. AUDITING /api/rpt-planilla/docentes (WITH DEV-LOGIN)")
    print("==================================================")
    res_rpt = client.get("/api/rpt-planilla/docentes", headers=headers)
    print(f"Status Code: {res_rpt.status_code}")
    try:
        data_rpt = res_rpt.json()
        print(f"Response (Truncated Data): success={data_rpt.get('success')}, error={data_rpt.get('error')}")
        if data_rpt.get("success"):
            print(f"Total list items returned: {len(data_rpt.get('data', {}).get('data', []))}")
            if len(data_rpt.get('data', {}).get('data', [])) > 0:
                print(f"Sample: {data_rpt.get('data', {}).get('data', [])[0]}")
    except Exception as e:
        print(f"Failed parsing response: {res_rpt.text} (Error: {e})")

    print("\n==================================================")
    print("5. AUDITING /api/schedule/teachers (WITH DEV-LOGIN)")
    print("==================================================")
    res_sch = client.get("/api/schedule/teachers", headers=headers)
    print(f"Status Code: {res_sch.status_code}")
    try:
        data_sch = res_sch.json()
        print(f"Response: success={data_sch.get('success')}, error={data_sch.get('error')}")
        if data_sch.get("success"):
            print(f"Total list items returned: {len(data_sch.get('data', {}).get('data', []))}")
    except Exception as e:
        print(f"Failed parsing response: {res_sch.text} (Error: {e})")

    print("\n==================================================")
    print("6. AUDITING /api/schedule/observations (WITH DEV-LOGIN)")
    print("==================================================")
    res_obs = client.get("/api/schedule/observations", headers=headers)
    print(f"Status Code: {res_obs.status_code}")
    try:
        data_obs = res_obs.json()
        print(f"Response: success={data_obs.get('success')}, error={data_obs.get('error')}")
        if data_obs.get("success"):
            print(f"Total list items returned: {len(data_obs.get('data', {}).get('data', []))}")
    except Exception as e:
        print(f"Failed parsing response: {res_obs.text} (Error: {e})")

    print("\n==================================================")
    print("7. AUDITING WITHOUT DEV-LOGIN (ANONYMOUS/RBAC CHECK)")
    print("==================================================")
    res_rpt_anon = client.get("/api/rpt-planilla/docentes")
    print(f"/api/rpt-planilla/docentes - Status: {res_rpt_anon.status_code} | Body: {res_rpt_anon.text}")
    res_sch_anon = client.get("/api/schedule/teachers")
    print(f"/api/schedule/teachers - Status: {res_sch_anon.status_code} | Body: {res_sch_anon.text}")
    res_obs_anon = client.get("/api/schedule/observations")
    print(f"/api/schedule/observations - Status: {res_obs_anon.status_code} | Body: {res_obs_anon.text}")

    db.close()

if __name__ == "__main__":
    run_audit()
