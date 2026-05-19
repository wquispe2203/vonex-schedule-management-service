import json
from fastapi.testclient import TestClient
from app.main import create_app
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

app.dependency_overrides[get_current_active_user] = lambda: MockUser()
app.dependency_overrides[require_permission("ver_rpt")] = lambda: True

client = TestClient(app)

def generate_snapshot(filename="snapshot_optimized.json"):
    print(f"Generating snapshot: {filename}...")
    params = {
        "fecha_inicio": "2026-03-02",
        "fecha_fin": "2026-03-08",
        "limit": 5000
    }
    response = client.get("/api/rpt-planilla/", params=params)
    if response.status_code == 200:
        full_res = response.json()
        data = full_res.get("data", {}).get("data", [])
        
        path = f"brain/632fbacc-9451-451a-805c-a4110b33cc72/scratch/{filename}"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
        print(f"Snapshot saved to {path}: {len(data)} consolidated records found.")
    else:
        print(f"FAILED to generate snapshot: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "snapshot_optimized.json"
    generate_snapshot(name)
