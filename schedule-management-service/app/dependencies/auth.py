from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.user import User, Role
from app.models.infrastructure import AuditLog
from app.core.security import SECRET_KEY, ALGORITHM
import json
import traceback

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

from app.core.observability import security_logger, log_event, set_user_id

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
            log_event(security_logger, "WARNING", "[AUTH FAILED]", "Token missing sub claim")
            raise credentials_exception
        
        user_id = UUID(user_id_str)
        set_user_id(user_id) # Set for observability context
    except JWTError as e:
        log_event(security_logger, "WARNING", "[AUTH FAILED]", f"JWT Error: {str(e)}")
        raise credentials_exception
    except ValueError as e:
        log_event(security_logger, "WARNING", "[AUTH FAILED]", f"UUID Format Error: {user_id_str}")
        raise credentials_exception

    try:
        user = db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions)
        ).filter(User.id == user_id).first()
        
        if user is None:
            log_event(security_logger, "WARNING", "[AUTH FAILED]", f"User not found: {user_id}")
            raise credentials_exception
        
        if not user.is_active:
            log_event(security_logger, "WARNING", "[AUTH FAILED]", f"Inactive user: {user.username}")
            raise credentials_exception
            
        return user
    except Exception as e:
        log_event(security_logger, "ERROR", "[AUTH CRITICAL]", str(e), {"stack": traceback.format_exc()})
        raise e

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def require_permission(permission_code: str):
    def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ):
        # 0. BYPASS SUPERADMIN
        is_protected_access = any(role.is_protected for role in current_user.roles)
        user_role_names = [role.name.upper() for role in current_user.roles]
        
        if is_protected_access:
            log_event(security_logger, "INFO", "[RBAC ACTION EXECUTED]", f"Access granted (Protected) to {permission_code}", {
                "user": current_user.username,
                "role_bypass": "protected_flag"
            })
            return current_user
            
        if "SUPERADMIN" in user_role_names:
            log_event(security_logger, "INFO", "[RBAC ACTION EXECUTED]", f"Access granted (Superadmin) to {permission_code}", {
                "user": current_user.username,
                "role_bypass": "string_match"
            })
            return current_user

        user_permissions = []
        for role in current_user.roles:
            user_permissions.extend([p.code for p in role.permissions])
        
        # 1. Validación Granular
        if permission_code not in user_permissions:
            log_event(security_logger, "WARNING", "[RBAC DENIED]", f"Missing permission: {permission_code}", {
                "user": current_user.username,
                "roles": user_role_names,
                "path": request.url.path
            })
            
            audit = AuditLog(usuario_id=current_user.id, accion=f"403_DENY_{permission_code}")
            db.add(audit); db.commit()

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido insuficiente: {permission_code}"
            )
            
        log_event(security_logger, "INFO", "[RBAC ACTION EXECUTED]", f"Permission verified: {permission_code}", {
            "user": current_user.username,
            "path": request.url.path
        })
        return current_user
        
    return permission_checker
