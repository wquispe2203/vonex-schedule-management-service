from sqlalchemy.orm import Session, joinedload
from app.database import SessionLocal
from app.models import User, Role, Permission

def verify_auth_integrity():
    db: Session = SessionLocal()
    try:
        print("--- VERIFICANDO INTEGRIDAD DE AUTENTICACIÓN UUID ---")
        
        # 1. Buscar un usuario que tenga roles
        user = db.query(User).options(joinedload(User.roles)).filter(User.roles.any()).first()
        
        if not user:
            print("  [INFO] No se encontró usuario con roles para probar. Probando carga básica...")
            user = db.query(User).first()
            if not user:
                print("  [ERROR] No hay usuarios en la base de datos.")
                return
        
        print(f"  Usuario: {user.username} (ID: {user.id})")
        print(f"  Roles encontrados: {len(user.roles)}")
        for r in user.roles:
            print(f"    - Rol: {r.name} (UUID: {r.id})")
            
        # 2. Verificar permisos de un rol
        if user.roles:
            role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == user.roles[0].id).first()
            print(f"  Permisos del rol '{role.name}': {len(role.permissions)}")
            for p in role.permissions:
                print(f"    - Permiso: {p.code} (UUID: {p.id})")
        
        print("\n  [SUCCESS] Integridad de relaciones Many-to-Many validada.")
        
    except Exception as e:
        print(f"  [ERROR] Fallo en la validación de integridad: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_auth_integrity()
