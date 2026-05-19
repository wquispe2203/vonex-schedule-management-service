from fastapi.testclient import TestClient
from app.main import create_app
from app.core.database import SessionLocal
from app.models import User
import json

def run():
    app = create_app()
    client = TestClient(app)
    
    # Let's inspect the actual response from the server for GET /api/rpt-planilla/docentes
    # Wait, we need to authenticate as a user. Let's see how login works.
    # In auth router, let's see how token is created. Or we can mock the auth dependency!
    # Let's override the require_permission dependency or get_current_active_user!
    from app.dependencies.auth import get_current_active_user
    
    db = SessionLocal()
    try:
        # Get various users
        admin = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        daacademica = db.query(User).filter(User.username == "daacademica@vonex.edu.pe").first()
        
        # We will query directly or override dependencies to see the payload
        print("=== MOCKING USERS FOR GET /api/rpt-planilla/docentes ===")
        
        # Helper to override user dependency
        def mock_user(user_obj):
            app.dependency_overrides[get_current_active_user] = lambda: user_obj
            
        # Test as admin@vonex.edu.pe
        mock_user(admin)
        print("\nQuerying as admin@vonex.edu.pe:")
        res = client.get("/api/rpt-planilla/docentes")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:300]}...")
        if res.status_code == 200:
            data = res.json()
            print(f"Success: {data.get('success')}")
            if data.get('success'):
                teachers = data['data']['data']
                print(f"Total teachers returned: {len(teachers)}")
                print(f"First 3: {teachers[:3]}")
                
        # Test as daacademica@vonex.edu.pe
        mock_user(daacademica)
        print("\nQuerying as daacademica@vonex.edu.pe:")
        res = client.get("/api/rpt-planilla/docentes")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:300]}...")
        
    finally:
        db.close()
        app.dependency_overrides.clear()

if __name__ == "__main__":
    run()
