import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_hard_cut_422():
    # Intentar enviar un ID numérico a un endpoint que espera UUID
    # POST /api/schedule/observations
    # El schema ObservationCreate espera teacher_id: UUID
    
    url = f"{BASE_URL}/api/schedule/observations"
    payload = {
        "teacher_id": 123,  # <--- ID NUMÉRICO (LEGACY)
        "session_id": "893c5d6e-1234-4321-abcd-1234567890ab",
        "type": "FALTA",
        "date": "2024-04-21"
    }
    
    print(f"Probando Hard-Cut en {url} con payload malicioso...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 422:
            print("SUCCESS: El backend rechazó el ID numérico con 422.")
            print("Respuesta del servidor:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"FAILURE: El backend no rechazó el ID numérico (Code: {response.status_code}).")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_hard_cut_422()
