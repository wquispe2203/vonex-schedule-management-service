import sys
import os
import traceback
import json
from fastapi.testclient import TestClient

# Asegurar que el path incluya la app
sys.path.append(os.getcwd())

from app.main import get_application

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzY5NzY5NjIsInN1YiI6ImM1YmYzN2NlLTgwNDctNGY4OC05ZDUwLTAyM2FjYzc1MzllZSJ9.gcZS1ijbhOoTbvia2ZI7anl79GSkgSYD7RRMKtHrWZA"

print("PHASE 1: STARTUP CHECK")
try:
    app = get_application()
    client = TestClient(app, raise_server_exceptions=True)
    print("SUCCESS: Application loaded successfully.")
except Exception as e:
    print("ERROR: STARTUP FAILED:")
    traceback.print_exc()
    sys.exit(1)

def run_diagnose(name, path):
    print(f"\n" + "="*80)
    print(f"PHASE 2: TESTING {name} -> {path}")
    print("="*80)
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = client.get(path, headers=headers)
        print(f"STATUS: {response.status_code}")
        print("RESPONSE JSON (truncated):")
        try:
            print(json.dumps(response.json(), indent=2)[:500])
        except:
            print("Response not JSON or empty")
    except Exception as e:
        print("\nPHASE 3: ROOT CAUSE DETECTED")
        print(f"ENDPOINT: {path}")
        print(f"EXCEPTION TYPE: {type(e).__name__}")
        print(f"CAUSE: {str(e)}")
        print("\nSTACKTRACE REAL:")
        traceback.print_exc()

if __name__ == "__main__":
    run_diagnose("USER ME", "/api/users/me")
    run_diagnose("CONFIG RECESOS", "/api/config/recesos")
    run_diagnose("CONFIG ALMUERZOS", "/api/config/almuerzos")
    run_diagnose("SCHEDULE TEACHERS", "/api/schedule/teachers")
