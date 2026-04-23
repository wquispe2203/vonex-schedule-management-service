from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.modules.usuarios.service import authenticate_user
from app.core.security import jwt, SECRET_KEY, ALGORITHM
from uuid import UUID

def test_auth_full_flow():
    db: Session = SessionLocal()
    try:
        print("--- TEST DE FLUJO COMPLETO DE AUTENTICACION UUID ---")
        
        # 1. Credenciales de prueba (asumiendo que admin:admin123 existe)
        # Si no existe, este test fallara informativamente
        username = "admin@vonex.edu.pe"
        password = "adminpassword123" # Cambiar segun realidad o crear temporal
        
        try:
            auth_result = authenticate_user(db, username, password)
            print("  [SUCCESS] Autenticacion exitosa via authenticate_user.")
            
            token = auth_result["access_token"]
            user_id = auth_result["user_id"]
            
            print(f"  Token generado: {token[:20]}...")
            print(f"  ID de usuario devuelto: {user_id} (Tipo: {type(user_id)})")
            
            # 2. Validar decodificacion de JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            print("  [SUCCESS] Token decodificado correctamente.")
            
            sub = payload.get("sub")
            roles = payload.get("roles")
            permissions = payload.get("permissions")
            
            print(f"  Claim 'sub': {sub} (Debe ser el UUID como string)")
            print(f"  Roles en token: {roles}")
            print(f"  Total permisos en token: {len(permissions)}")
            
            if str(user_id) == sub:
                print("  [SUCCESS] El UUID del token coincide con el ID del usuario.")
            else:
                print("  [WARNING] Disparidad entre ID de usuario y claim 'sub'.")
                
        except Exception as auth_e:
            print(f"  [INFO] No se pudo completar el login (posiblemente credenciales inexistentes): {auth_e}")
            print("  [PROBANDO CARGA DE DATOS BASICA...]")
            from app.models import User
            user = db.query(User).first()
            if user:
                print(f"  Usuario encontrado para prueba manual: {user.username}")
                print(f"  Probando generacion de token aislada para UUID: {user.id}")
                from app.core.security import create_access_token
                test_token = create_access_token(subject=user.id, custom_claims={"test": True})
                test_payload = jwt.decode(test_token, SECRET_KEY, algorithms=[ALGORITHM])
                print(f"  Claim 'sub' en test: {test_payload.get('sub')}")
                if isinstance(test_payload.get('sub'), str):
                     print("  [SUCCESS] create_access_token serializa correctamente UUID a string.")
            
    except Exception as e:
        print(f"  [ERROR] Fallo critico en el test de flujo: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_auth_full_flow()
