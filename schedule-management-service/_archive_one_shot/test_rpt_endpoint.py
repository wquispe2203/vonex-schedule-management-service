import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/rpt-planilla/docentes"

def test_rpt_teachers_endpoint():
    print(f"Testing endpoint: {BASE_URL}{ENDPOINT}")
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Success!")
            print(f"Total teachers returned: {len(data.get('data', []))}")
            if len(data.get('data', [])) > 0:
                print("First 5 teachers:")
                for teacher in data['data'][:5]:
                    print(f" - {teacher}")
            else:
                print("WARNING: No teachers returned. Verify if teachers have 'is_active=True' and activity (lessons/observations).")
        else:
            print(f"ERROR: {response.text}")
            
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")

if __name__ == "__main__":
    test_rpt_teachers_endpoint()
