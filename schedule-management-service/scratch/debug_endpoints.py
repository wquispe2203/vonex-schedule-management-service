import sys
import os
from fastapi.testclient import TestClient
import traceback

# Asegurar que el path incluya la app
sys.path.append(os.getcwd())

from app.main import get_application
from app.database import SessionLocal

app = get_application()
client = TestClient(app)

def debug_endpoint(path, headers=None):
    print(f"\n{'='*50}")
    print(f"DEBUGGING ENDPOINT: {path}")
    print(f"{'='*50}")
    try:
        response = client.get(path, headers=headers)
        print(f"Status Code: {response.status_code}")
        try:
            print("Response JSON:")
            import json
            print(json.dumps(response.json(), indent=2))
        except:
            print("Response Text (Not JSON):")
            print(response.text)
            
        if response.status_code == 500:
            print("\n!!! ERROR 500 DETECTADO !!!")
            # El traceback debería ser visible en la consola por el global_exception_handler
            # Pero forzaremos una inspección si es posible.
            
    except Exception as e:
        print(f"Falla crítica al invocar endpoint: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # 1. Health check
    debug_endpoint("/health")
    
    # 2. Endpoints de Configuración
    debug_endpoint("/api/config/recesos")
    debug_endpoint("/api/config/almuerzos")
    
    # 3. Endpoints de Horarios
    debug_endpoint("/api/schedule/teachers")
    
    # 4. Endpoints Protegidos (Sin token para ver si el error es 401 o 500)
    debug_endpoint("/api/users/me")
