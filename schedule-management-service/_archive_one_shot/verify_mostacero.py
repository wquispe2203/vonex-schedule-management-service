import requests
import json

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/rpt-planilla/docentes"

def verify_mostacero():
    print(f"Verifying 'MOSTACERO' in: {BASE_URL}{ENDPOINT}")
    try:
        response = requests.get(f"{BASE_URL}{ENDPOINT}")
        if response.status_code == 200:
            data = response.json().get('data', [])
            found = [t for t in data if "MOSTACERO" in t.upper()]
            if found:
                print(f"SUCCESS! Teacher found in RPT list: {found}")
            else:
                print("FAILURE: Teacher still NOT FOUND in RPT list.")
        else:
            print(f"API Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_mostacero()
