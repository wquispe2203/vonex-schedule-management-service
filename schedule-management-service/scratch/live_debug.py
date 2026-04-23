import httpx
from uuid import UUID
import json

def test_endpoint(name, url):
    print(f"\n--- Probando {name} ({url}) ---")
    try:
        # Usamos un timeout corto para detectar si el servidor está colgado
        response = httpx.get(url, timeout=10.0)
        print(f"Status: {response.status_code}")
        try:
            print(json.dumps(response.json(), indent=2))
        except:
            print("Response Text (No JSON):", response.text[:200])
    except Exception as e:
        print(f"Error al conectar: {e}")

if __name__ == "__main__":
    BASE_URL = "http://localhost:8000"
    test_endpoint("Health", f"{BASE_URL}/health")
    test_endpoint("Users Me", f"{BASE_URL}/api/users/me")
    test_endpoint("Config Recesos", f"{BASE_URL}/api/config/recesos")
    test_endpoint("Config Almuerzos", f"{BASE_URL}/api/config/almuerzos")
    test_endpoint("Schedule Teachers", f"{BASE_URL}/api/schedule/teachers")
