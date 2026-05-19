from fastapi.testclient import TestClient
from app.main import create_app
from app.core.database import SessionLocal
from app.models import Teacher
from app.dependencies.auth import get_current_active_user
import json

def run():
    app = create_app()
    client = TestClient(app)
    
    db = SessionLocal()
    try:
        from sqlalchemy import text
        
        print("=== DIRECT SQL AUDIT ON TEACHERS TABLES ===")
        
        # 1. Row count of teachers with status = 'INCOMPLETO' or 'CONFLICTO'
        res_statuses = db.execute(text("SELECT status, COUNT(*) FROM teachers GROUP BY status")).all()
        print("\nTeachers by Status in 'teachers' table:")
        for r in res_statuses:
            print(f"  - Status: {r[0]}, Count: {r[1]}")
            
        # 2. Check if 'teachers_sinasignar' table exists and has rows on PostgreSQL
        table_exists = db.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_name='teachers_sinasignar'"
        )).first()
        if table_exists:
            print("\nTable 'teachers_sinasignar' exists!")
            rows = db.execute(text("SELECT COUNT(*) FROM teachers_sinasignar")).scalar()
            print(f"  - Total rows: {rows}")
            if rows > 0:
                sample = db.execute(text("SELECT * FROM teachers_sinasignar LIMIT 5")).all()
                print("  - Sample rows:")
                for s in sample:
                    print(f"    {s}")
        else:
            print("\nTable 'teachers_sinasignar' does NOT exist!")
            
        # 3. Simulate calling GET /api/docentes/sinasignar as admin@vonex.edu.pe
        admin = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
        app.dependency_overrides[get_current_active_user] = lambda: admin
        
        print("\nQuerying GET /api/docentes/sinasignar as admin:")
        res = client.get("/api/docentes/sinasignar")
        print(f"Status Code: {res.status_code}")
        print(f"Response: {res.text[:400]}...")
        
    finally:
        db.close()
        app.dependency_overrides.clear()

if __name__ == "__main__":
    from app.models import User
    run()
