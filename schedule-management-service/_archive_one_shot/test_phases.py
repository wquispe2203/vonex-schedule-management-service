import sys
from datetime import date
from sqlalchemy import text
from app.core.database import SessionLocal
from fastapi.testclient import TestClient
from app.main import create_app
from app.dependencies.auth import get_current_user

app = create_app()

def override_get_current_user():
    class MockPerm:
        def __init__(self, c): self.code = c
    class MockRole:
        name = "ADMIN"
        permissions = [MockPerm("ver_horarios"), MockPerm("ver_rpt"), MockPerm("admin")]
    class MockUser:
        id = "098b90ea-5ff5-4ee3-a8cc-d8e3c1aca1dd"
        username = "test@test.com"
        email = "test@test.com"
        is_active = True
        roles = [MockRole()]
    return MockUser()

app.dependency_overrides[get_current_user] = override_get_current_user
client = TestClient(app)

print('GET /api/schedule/xml-uploads')
r1 = client.get('/api/schedule/xml-uploads')
print('Status:', r1.status_code)
if r1.status_code == 200:
    data = r1.json()
    print(f'JSON RESPONSE: {data}')
else:
    print(r1.text)

print('\nGET /api/rpt-planilla/?fecha_inicio=2026-03-02&fecha_fin=2026-03-08')
r2 = client.get('/api/rpt-planilla/?fecha_inicio=2026-03-02&fecha_fin=2026-03-08')
print('Status:', r2.status_code)
if r2.status_code == 200:
    data = r2.json()
    print(f"Data count: {len(data.get('data', []))}")
else:
    print(r2.text)
