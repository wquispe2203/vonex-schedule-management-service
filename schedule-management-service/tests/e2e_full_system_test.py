import os
import sys
import pytest
from fastapi.testclient import TestClient

# 1. FORZAR ENTORNO DE TESTING
os.environ["TESTING"] = "True"

# Asegurar que el modulo app sea visible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import engine, SessionLocal
from app.models import Base

# Cliente de pruebas
client = TestClient(app)

def test_full_system_flow():
    """
    FLUJO POSITIVO: Login real -> Token -> /me -> Data
    """
    print("\n--- INICIANDO E2E COMPLETO (SISTEMA REAL EN MODO TEST) ---")
    
    # A. LOGIN REAL (Sin bypass)
    login_data = {
        "username": "admin_test@vonex.edu.pe",
        "password": "TestAdmin123!"
    }
    response = client.post("/api/users/login", data=login_data)
    
    assert response.status_code == 200, f"Login fallido: {response.text}"
    token_data = response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("  [SUCCESS] Login autentico completado.")

    # B. VALIDACION DE SESION (/me)
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    
    assert user_data["username"] == "admin_test@vonex.edu.pe"
    assert "permissions" in user_data
    assert isinstance(user_data["permissions"], list)
    assert "ver_horarios" in user_data["permissions"]
    
    print("  [SUCCESS] Sesion (/me) validada con permisos aplanados.")

    # C. VALIDACION DE DATOS (Teachers)
    response = client.get("/api/schedule/teachers", headers=headers)
    assert response.status_code == 200
    teachers_json = response.json()
    
    assert teachers_json["success"] is True
    assert len(teachers_json["data"]) > 0
    teacher = teachers_json["data"][0]
    
    # VALIDACION CRITICA: Contrato DTO UUID mapping
    assert "id" in teacher
    assert "uid" in teacher
    assert str(teacher["id"]) == teacher["uid"], "El mapeo uid -> id no es consistente"
    
    print("  [SUCCESS] Listado de docentes validado (id/uid mapping OK).")

    # D. VALIDACION DE CONFIGURACION
    response = client.get("/api/config/recesos", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    print("  [SUCCESS] Configuracion accesible.")

def test_security_audit_negative():
    """
    AUDITORIA NEGATIVA: Validar que la seguridad REAL bloquea accesos invalidos
    """
    print("\n--- INICIANDO AUDITORIA DE SEGURIDAD NEGATIVA ---")

    # 1. Acceso sin token
    response = client.get("/api/users/me")
    assert response.status_code == 401
    print("  [SUCCESS] Bloqueo correcto por falta de credenciales (401).")

    # 2. Token invalido
    response = client.get("/api/users/me", headers={"Authorization": "Bearer token_falso"})
    assert response.status_code == 401
    print("  [SUCCESS] Bloqueo correcto por token mal formado (401).")

    # 3. Credenciales incorrectas
    response = client.post("/api/users/login", data={"username": "admin_test@vonex.edu.pe", "password": "wrong_password"})
    assert response.status_code == 401
    print("  [SUCCESS] Login denegado con password incorrecto.")

if __name__ == "__main__":
    # Ejecucion manual
    try:
        test_full_system_flow()
        test_security_audit_negative()
        print("\n==========================================")
        print("ALL E2E TESTS PASSED (TEST MODE)")
        print("==========================================")
    except Exception as e:
        print(f"\nERROR IN E2E TESTS: {e}")
        sys.exit(1)
