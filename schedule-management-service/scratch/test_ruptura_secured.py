import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_422_test():
    print("--- 422 RUPTURE TEST (SECURED) ---")
    
    # 1. Login
    login_url = f"{BASE_URL}/api/users/login"
    login_data = {"username": "admin@vonex.edu.pe", "password": "Admin123!"}
    
    print(f"Intentando login en {login_url}...")
    try:
        login_res = requests.post(login_url, data=login_data)
        if login_res.status_code != 200:
            print(f"Error en login (Code: {login_res.status_code}): {login_res.text}")
            return
        
        token = login_res.json()["access_token"]
        print("Login exitoso. Token obtenido.")
        
        # 2. Test 422
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        obs_url = f"{BASE_URL}/api/schedule/observations"
        
        payload = {
            "teacher_id": 123,  # <--- DATO NUMÉRICO PROHIBIDO
            "session_id": "893c5d6e-1234-4321-abcd-1234567890ab",
            "type": "FALTA",
            "date": "2024-04-21"
        }
        
        print(f"Enviando payload con ID numérico a {obs_url}...")
        obs_res = requests.post(obs_url, headers=headers, json=payload)
        
        print(f"Status Code: {obs_res.status_code}")
        if obs_res.status_code == 422:
            print("SUCCESS: El backend rechazó correctamente el ID numérico con HTTP 422.")
            print("Mensaje de error (Pydantic):")
            print(json.dumps(obs_res.json(), indent=2))
        else:
            print(f"FAILURE: El sistema permitió un ID numérico o devolvió un error inesperado (Code: {obs_res.status_code}).")
            if obs_res.status_code != 200:
                 print(obs_res.text)
            
    except Exception as e:
        print(f"System Error: {e}")

if __name__ == "__main__":
    run_422_test()
