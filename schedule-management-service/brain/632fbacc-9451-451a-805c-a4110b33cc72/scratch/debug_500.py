from fastapi.testclient import TestClient
from app.main import create_app
from app.dependencies.auth import require_permission, get_current_active_user
import traceback
import sys

def debug():
    try:
        app = create_app()
        # Mock Auth
        app.dependency_overrides[get_current_active_user] = lambda: type('U',(),{'id':'0','username':'a','roles':[type('R',(),{'is_protected':True,'name':'ADMIN'})]})()
        app.dependency_overrides[require_permission('ver_rpt')] = lambda: True
        
        client = TestClient(app)
        print("Starting request...")
        r = client.get('/api/rpt-planilla/', params={'fecha_inicio':'2026-03-01', 'fecha_fin':'2026-03-31'})
        print(f"Status Code: {r.status_code}")
        if r.status_code != 200:
            print("Response Body:")
            print(r.text)
        else:
            print("SUCCESS")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    debug()
