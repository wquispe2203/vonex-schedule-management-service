from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from typing import Dict, Any, List
from uuid import UUID

DOMAIN_REQUIRED = "@vonex.edu.pe"

def create_user(db: Session, data: Dict[str, Any]) -> User:
    username = data.get("username", "").strip().lower()
    
    # 1. Validación en creación de usuario (OBLIGATORIO)
    if not username.endswith(DOMAIN_REQUIRED):
        raise ValueError(f"El usuario debe registrarse con un email de la institución ({DOMAIN_REQUIRED}).")
        
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise ValueError("El usuario ya existe.")
        
    password = data.pop("password", None)
    if not password:
        raise ValueError("La contraseña es requerida.")

    hashed_pw = get_password_hash(password)
    
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"[USERS CREATE DB INSERT] Inserting user into DB: {username}")

    new_user = User(
        username=username,
        password_hash=hashed_pw,
        nombres=data.get("nombres"),
        apellidos=data.get("apellidos"),
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"[USERS CREATE DB INSERT SUCCESS] User created with UUID: {new_user.id}")
    return new_user

def authenticate_user(db: Session, username: str, password: str) -> Dict[str, Any]:
    username = username.strip().lower()
    
    # 2. Validación en login (Capa adicional de seguridad)
    if not username.endswith(DOMAIN_REQUIRED):
        raise ValueError(f"Dominio inválido. Se requiere acceso mediante Email institucional ({DOMAIN_REQUIRED}).")
        
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise ValueError("Credenciales incorrectas")
    
    # Soporte temporal si tuviera password null por migración
    if not user.password_hash or not verify_password(password, user.password_hash):
        raise ValueError("Credenciales incorrectas")
        
    if not user.is_active:
        raise ValueError("El usuario se encuentra inactivo")
        
    roles = [r.name.upper() for r in user.roles]
    
    # Recopilar códigos de permisos granulares
    user_permissions = []
    for role in user.roles:
        user_permissions.extend([p.code for p in role.permissions])
    
    # Eliminar duplicados
    user_permissions = list(set(user_permissions))
    
    # Flag de superusuario para bypass en frontend
    is_superadmin = "SISTEMAS" in roles or "SUPERADMIN" in roles
    
    claims = {
        "roles": roles,
        "username": user.username,
        "permissions": user_permissions,
        "is_superadmin": is_superadmin
    }
    
    access_token = create_access_token(subject=user.id, custom_claims=claims)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username
    }

# --- CRUD USUARIOS ---
def get_users(db: Session):
    from sqlalchemy.orm import joinedload
    return db.query(User).options(joinedload(User.roles)).all()

def update_user(db: Session, user_id: UUID, data: Dict[str, Any]):
    import logging
    logger = logging.getLogger("uvicorn")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"[USERS UPDATE ORM] User not found on lookup. ID: {user_id}")
        raise ValueError("Usuario no encontrado")

    # Regla de validación estricta de Username y Dominio
    username = data.get("username")
    if username is not None:
        username = username.strip().lower()
        if not username.endswith(DOMAIN_REQUIRED):
            raise ValueError(f"El usuario debe registrarse con un email de la institución ({DOMAIN_REQUIRED}).")
            
        existing = db.query(User).filter(User.username == username, User.id != user_id).first()
        if existing:
            raise ValueError("El correo ingresado ya está en uso por otra cuenta.")
        data["username"] = username

    logger.info(f"[USERS UPDATE ORM] Updating ORM fields for user_id={user_id}. Payload attributes: {list(data.keys())}")
    for k, v in data.items():
        if hasattr(user, k):
            setattr(user, k, v)
            
    logger.info(f"[USERS UPDATE COMMIT] Triggering database commit for user_id={user_id}")
    db.commit()
    logger.info(f"[USERS UPDATE COMMIT] Executing user object refresh")
    db.refresh(user)
    return user

def delete_user(db: Session, user_id: UUID):
    import logging
    logger = logging.getLogger("uvicorn")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    logger.info(f"[RBAC DELETE AUTHORIZED] Desactivando el acceso del usuario '{user.username}' con ID: {user_id}")
    user.is_active = False
    db.commit()
    return user

def assign_roles_to_user(db: Session, user_id: UUID, role_ids: List[UUID]):
    from app.models import Role
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
        
    roles = db.query(Role).filter(Role.id.in_(role_ids)).all()
    user.roles = roles
    db.commit()
    db.refresh(user)
    return user

# --- CRUD ROLES ---
def get_roles(db: Session):
    from app.models import Role
    from sqlalchemy.orm import joinedload
    return db.query(Role).options(joinedload(Role.permissions)).all()

def create_role(db: Session, name: str):
    from app.models import Role
    n = name.strip().upper()
    existing = db.query(Role).filter(Role.name == n).first()
    if existing:
        raise ValueError("El rol ya existe")
    role = Role(name=n)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

def assign_permissions_to_role(db: Session, role_id: UUID, permission_ids: List[UUID]):
    from app.models import Role, Permission
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise ValueError("Rol no encontrado")
        
    perms = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    role.permissions = perms
    db.commit()
    db.refresh(role)
    return role

def update_role(db: Session, role_id: UUID, new_name: str):
    from app.models import Role
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise ValueError("Rol no encontrado")
        
    PROTECTED_ROLES = ["SUPERADMIN", "SISTEMAS"]
    if role.is_protected or role.name.upper() in PROTECTED_ROLES:
        import logging
        logger = logging.getLogger("uvicorn")
        logger.warning(f"[PROTECTED ROLE BLOCKED] Attempted to RENAME protected role: {role.name}")
        raise ValueError(f"No está permitido editar el nombre de un rol estructural protegido: {role.name}")
        
    n = new_name.strip().upper()
    existing = db.query(Role).filter(Role.name == n, Role.id != role_id).first()
    if existing:
        raise ValueError("Ya existe otro rol registrado con ese nombre.")
        
    role.name = n
    db.commit()
    db.refresh(role)
    return role

def delete_role(db: Session, role_id: UUID):
    from app.models import Role
    import logging
    logger = logging.getLogger("uvicorn")
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise ValueError("Rol no encontrado")
        
    PROTECTED_ROLES = ["SUPERADMIN", "SISTEMAS"]
    if role.is_protected or role.name.upper() in PROTECTED_ROLES:
        logger.warning(f"[PROTECTED ROLE BLOCKED] Attempted to DELETE protected role: {role.name}")
        raise ValueError(f"No está permitido eliminar un rol estructural protegido: {role.name}")
        
    logger.info(f"[RBAC DELETE AUTHORIZED] Procediendo a la eliminación física del rol '{role.name}' con ID: {role_id}")
    db.delete(role)
    db.commit()
    return True

# --- CRUD PERMISOS ---
def get_permissions(db: Session):
    from app.models import Permission
    return db.query(Permission).all()

def update_user_password(db: Session, user_id: UUID, new_password: str):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    
    if len(new_password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres")
        
    user.password_hash = get_password_hash(new_password)
    db.commit()
    return user
