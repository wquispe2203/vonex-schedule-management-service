from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import User, Role, AuditLog
from app.core.security import SECRET_KEY, ALGORITHM
import json
import traceback

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            print("[AUTH] Token sin claim 'sub'")
            raise credentials_exception
        
        # Log para debug (Solo en desarrollo)
        print(f"[AUTH] Validando sub: {user_id_str}")
        
        user_id = UUID(user_id_str)
    except JWTError as e:
        print(f"[AUTH] JWT Error: {str(e)}")
        raise credentials_exception
    except ValueError as e:
        print(f"[AUTH] UUID Format Error: {user_id_str} no es un UUID válido. {str(e)}")
        raise credentials_exception

    try:
        user = db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions)
        ).filter(User.id == user_id).first()
        
        if user is None:
            print(f"[AUTH] Usuario no encontrado en DB: {user_id}")
            raise credentials_exception
        
        if not user.is_active:
            print(f"[AUTH] Usuario inactivo: {user.username}")
            raise credentials_exception
            
        return user
    except Exception as e:
        print(f"!!! [AUTH] ERROR CRITICO en get_current_user: {str(e)}")
        traceback.print_exc()
        raise e


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def require_permission(permission_code: str):
    """
    Dependency generator para RBAC con auditoría detallada.
    """
    def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        user_role_names = [role.name.upper() for role in current_user.roles]
        user_permissions = []
        for role in current_user.roles:
            user_permissions.extend([p.code for p in role.permissions])
        
        # Log base para stdout
        log_msg = f"[AUTH] Usuario: {current_user.username} | Roles: {user_role_names} | Intentando: {permission_code} | Path: {request.url.path}"
        
        # 1. Validación Granular (SIN BYPASS)
        if permission_code not in user_permissions:
            print(f"{log_msg} | Resultado: DENY (403)")
            
            # Auditoría en DB para acceso denegado
            audit = AuditLog(
                usuario_id=current_user.id,
                accion=f"403_DENY_{permission_code}"
            )
            db.add(audit)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido insuficiente: {permission_code}"
            )
            
        print(f"{log_msg} | Resultado: ALLOW")
        return current_user
        
    return permission_checker
