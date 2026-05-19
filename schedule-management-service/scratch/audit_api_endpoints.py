import os
import sys
import json
from pathlib import Path

# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from fastapi.testclient import TestClient
    from app.main import create_app
    from app.core.database import SessionLocal
    from app.dependencies.auth import get_current_active_user, require_permission
    from app.models import User
    from uuid import UUID
    
    app = create_app()
    
    class MockRole:
        name = "SUPERADMIN"
        is_protected = True
        
    class MockUser:
        id = UUID("00000000-0000-0000-0000-000000000000")
        username = "admin"
        roles = [MockRole()]
        is_active = True
        
    app.dependency_overrides[get_current_active_user] = lambda: MockUser()
    app.dependency_overrides[require_permission("gestionar_docentes")] = lambda: True
    app.dependency_overrides[require_permission("ver_docentes")] = lambda: True
    
    client = TestClient(app)
    
    print("--- TESTING API ENDPOINTS ---")
    
    # 1. GET /api/docentes/sinasignar
    res_sa = client.get("/api/docentes/sinasignar")
    print(f"GET /api/docentes/sinasignar status_code: {res_sa.status_code}")
    print(f"Response shape keys: {list(res_sa.json().keys()) if res_sa.status_code == 200 else res_sa.text}")
    if res_sa.status_code == 200:
        data = res_sa.json().get("data", {})
        print(f"  Total items: {data.get('total')}")
        print(f"  Page: {data.get('page')}")
        print(f"  Limit: {data.get('limit')}")
        print(f"  Data items count: {len(data.get('data', []))}")
        
    # 2. GET /api/docentes/conflictos
    res_conf = client.get("/api/docentes/conflictos")
    print(f"\nGET /api/docentes/conflictos status_code: {res_conf.status_code}")
    print(f"Response shape keys: {list(res_conf.json().keys()) if res_conf.status_code == 200 else res_conf.text}")
    if res_conf.status_code == 200:
        data = res_conf.json().get("data", {})
        print(f"  Total items: {data.get('total')}")
        print(f"  Page: {data.get('page')}")
        print(f"  Limit: {data.get('limit')}")
        print(f"  Data items count: {len(data.get('data', []))}")
        
    # Clean up overrides
    app.dependency_overrides.clear()
    
    # Save API validation results
    validation_data = {
        "sin_asignar_endpoint": {
            "status_code": res_sa.status_code,
            "success": res_sa.json().get("success") if res_sa.status_code == 200 else False,
            "total": res_sa.json().get("data", {}).get("total") if res_sa.status_code == 200 else 0
        },
        "conflictos_endpoint": {
            "status_code": res_conf.status_code,
            "success": res_conf.json().get("success") if res_conf.status_code == 200 else False,
            "total": res_conf.json().get("data", {}).get("total") if res_conf.status_code == 200 else 0
        }
    }
    
    out_path = Path("d:/Desktop/MOD HOR/schedule-management-service/scratch/crossing_api_validation.json")
    out_path.write_text(json.dumps(validation_data, indent=2), encoding="utf-8")
    print(f"\nAPI validation results successfully saved to {out_path}")
    
except Exception as e:
    import traceback
    print(f"Error testing API endpoints: {str(e)}")
    traceback.print_exc()
