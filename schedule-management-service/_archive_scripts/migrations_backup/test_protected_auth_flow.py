from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.modules.usuarios.service import authenticate_user
from app.dependencies.auth import get_current_user
from app.models import User
from uuid import UUID

def test_protected_auth_flow():
    db: Session = SessionLocal()
    try:
        print("--- TEST DE FLUJO E2E: RUTAS PROTEGIDAS CON UUID ---")
        
        # 1. Obtener un usuario real para la prueba
        user = db.query(User).first()
        if not user:
            print("  [ERROR] No hay usuarios para probar.")
            return
            
        print(f"  Probando con usuario: {user.username} (ID: {user.id})")
        
        # 2. Simular generación de token
        from app.core.security import create_access_token
        # El claim 'sub' contendrá el UUID como string
        roles = [r.name.upper() for r in user.roles]
        token = create_access_token(subject=user.id, custom_claims={"roles": roles})
        print(f"  Token generado exitosamente.")
        
        # 3. Simular llamada a dependencia get_current_user
        # get_current_user(token, db) decodificará 'sub', lo convertirá a UUID y buscará en DB
        identified_user = get_current_user(token=token, db=db)
        
        print(f"  Usuario identificado por middleware: {identified_user.username}")
        print(f"  ID identificado: {identified_user.id} (Tipo: {type(identified_user.id)})")
        
        if identified_user.id == user.id:
            print("  [SUCCESS] Identificación E2E impecable: UUID -> JWT -> UUID -> DB Match.")
        else:
            print(f"  [ERROR] Discordancia de identidad: {identified_user.id} != {user.id}")
            
        # 4. Validar que no hay residuos 'int' en la identificación
        if not isinstance(identified_user.id, UUID):
            print("  [WARNING] El ID identificado no es un objeto UUID.")
            
    except Exception as e:
        print(f"  [ERROR] Fallo en la validación de flujo protegido: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_protected_auth_flow()
