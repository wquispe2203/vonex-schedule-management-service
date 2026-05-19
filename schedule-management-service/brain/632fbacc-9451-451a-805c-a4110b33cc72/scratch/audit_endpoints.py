import time
import json
from fastapi.testclient import TestClient
from app.main import create_app
from app.core.database import SessionLocal
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.dependencies.auth import require_permission, get_current_active_user

app = create_app()

# Bypass Auth
class MockRole:
    def __init__(self, is_protected=False):
        self.is_protected = is_protected
        self.name = "ADMIN"

class MockUser:
    def __init__(self):
        self.id = "00000000-0000-0000-0000-000000000000"
        self.username = "admin"
        self.roles = [MockRole(is_protected=True)]

def mock_user():
    return MockUser()

def mock_perm():
    return True

app.dependency_overrides[get_current_active_user] = mock_user
app.dependency_overrides[require_permission("ver_rpt")] = mock_perm
app.dependency_overrides[require_permission("ver_docentes")] = mock_perm

client = TestClient(app)

# Query counter
queries = []

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    queries.append(statement)

def audit_endpoint(name, url, params=None):
    global queries
    queries = []
    start_time = time.perf_counter()
    response = client.get(url, params=params)
    duration = (time.perf_counter() - start_time) * 1000
    payload_size = len(response.content) / 1024 # KB
    
    print(f"--- AUDIT: {name} ---")
    print(f"URL: {url}")
    print(f"Status: {response.status_code}")
    print(f"Duration: {duration:.2f}ms")
    print(f"Payload: {payload_size:.2f} KB")
    print(f"Query Count: {len(queries)}")
    # print("Queries:")
    # for q in queries[:5]: print(f"  {q[:100]}...")
    print("-" * 30)
    return {
        "name": name,
        "duration_ms": duration,
        "query_count": len(queries),
        "status": response.status_code
    }

if __name__ == "__main__":
    # Test RPT main endpoint with REAL data
    audit_endpoint("RPT Main (March 2026)", "/api/rpt-planilla/", params={
        "fecha_inicio": "2026-03-01",
        "fecha_fin": "2026-03-31"
    })
    
    # Test Docentes with Hours (The slow one)
    audit_endpoint("Docentes Hours", "/api/rpt-planilla/docentes")
    
    # Test Sede list
    audit_endpoint("Sedes", "/api/rpt-planilla/sedes")
