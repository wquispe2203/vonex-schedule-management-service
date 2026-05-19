from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.dependencies.auth import require_permission
from app.core.schemas import StandardResponse, PaginatedResponseData
from . import schemas, service
from app.models import User

router = APIRouter(prefix="/api/users", tags=["Users & Security"])
rbac_router = APIRouter(prefix="/api", tags=["Roles & Permissions"])

@router.post("", response_model=schemas.UserStandardResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    import logging
    import traceback
    logger = logging.getLogger("uvicorn")
    
    payload = user_data.model_dump()
    logger.info(f"[USERS CREATE PAYLOAD] Received new user request: {payload}")
    
    try:
        logger.info("[USERS CREATE VALIDATION] Proceeding with username validation.")
        user = service.create_user(db, payload)
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        logger.warning(f"[USERS CREATE VALIDATION ERROR] {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"[USERS CREATE ERROR TRACE] Critical error registering user:\n{tb}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno: {str(e)}")

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        data = service.authenticate_user(db, form_data.username, form_data.password)
        return schemas.Token(access_token=data["access_token"], token_type=data["token_type"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.get("/dev-login", response_model=schemas.Token)
def dev_login(db: Session = Depends(get_db)):
    from app.core.config import settings
    if not settings.is_development:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This endpoint is only available in development mode.")
    
    # Priorizar la autenticación del Superadmin real (admin@vonex.edu.pe)
    user = db.query(User).filter(User.username == "admin@vonex.edu.pe").first()
    if not user:
        # Fallback to another systems admin or superadmin if admin is not found
        from app.models import Role
        user = db.query(User).join(User.roles).filter(Role.name.in_(["SUPERADMIN", "SISTEMAS"])).first()
    if not user:
        # Fallback to the first active user
        user = db.query(User).filter(User.is_active == True).first()
        
    if not user:
        raise HTTPException(status_code=404, detail="No users found in database to impersonate.")
    
    # Generar claims completos para evitar que falten permisos en el frontend durante hidratación
    roles = [r.name.upper() for r in user.roles]
    user_permissions = []
    for role in user.roles:
        user_permissions.extend([p.code for p in role.permissions])
    user_permissions = list(set(user_permissions))
    is_superadmin = "SISTEMAS" in roles or "SUPERADMIN" in roles
    
    claims = {
        "roles": roles,
        "username": user.username,
        "permissions": user_permissions,
        "is_superadmin": is_superadmin
    }
    
    access_token = service.create_access_token(subject=user.id, custom_claims=claims)
    return schemas.Token(access_token=access_token, token_type="bearer")

# --- ENDPOINTS USUARIOS ---
from typing import List
from app.dependencies.auth import get_current_user

@router.get("/me", response_model=schemas.UserStandardResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": current_user, "error": None}

@router.get("", response_model=schemas.UserListStandardResponse)
def get_all_users(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    users = service.get_users(db)
    return {
        "success": True,
        "data": {
            "data": users,
            "total": len(users),
            "page": 1,
            "limit": len(users),
            "total_pages": 1
        },
        "error": None
    }

@router.put("/{user_id}", response_model=schemas.UserStandardResponse)
def update_user(user_id: UUID, user_data: schemas.UserBase, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"[USERS UPDATE REQUEST] Recibida solicitud PUT para usuario_id={user_id}")
    try:
        payload = user_data.model_dump(exclude_unset=True)
        logger.info(f"[USERS UPDATE PAYLOAD] Datos a actualizar: {payload}")
        user = service.update_user(db, user_id, payload)
        logger.info(f"[USERS UPDATE RESPONSE] Usuario actualizado satisfactoriamente: {user_id}")
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        logger.warning(f"[USERS UPDATE ERROR] Error de validación en PUT /users: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        logger.error(f"[USERS UPDATE ERROR] Fallo inesperado del servidor en PUT /users: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.put("/{user_id}/password", response_model=schemas.StandardResponse[None])
def change_password(user_id: UUID, payload: schemas.PasswordChange, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        service.update_user_password(db, user_id, payload.new_password)
        return {"success": True, "data": None, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}", response_model=schemas.UserStandardResponse)
def deactivate_user(user_id: UUID, db: Session = Depends(get_db), _ = Depends(require_permission("eliminar_usuarios"))):
    try:
        user = service.delete_user(db, user_id)
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_id}/roles", response_model=schemas.UserStandardResponse)
def assign_roles(user_id: UUID, payload: schemas.RoleAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        user = service.assign_roles_to_user(db, user_id, payload.role_ids)
        return {"success": True, "data": user, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS ROLES (RBAC) ---
@rbac_router.get("/roles", response_model=schemas.RoleListStandardResponse)
def get_all_roles(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    roles = service.get_roles(db)
    return {
        "success": True,
        "data": {
            "data": roles,
            "total": len(roles),
            "page": 1,
            "limit": len(roles),
            "total_pages": 1
        },
        "error": None
    }

@rbac_router.post("/roles", response_model=schemas.RoleStandardResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: schemas.RoleCreate, db: Session = Depends(get_db), _ = Depends(require_permission("crear_roles"))):
    try:
        role = service.create_role(db, payload.name)
        return {"success": True, "data": role, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@rbac_router.post("/roles/{role_id}/permissions", response_model=schemas.RoleStandardResponse)
def assign_permissions(role_id: UUID, payload: schemas.PermissionAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_permisos"))):
    try:
        role = service.assign_permissions_to_role(db, role_id, payload.permission_ids)
        return {"success": True, "data": role, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS PERMISOS (RBAC) ---
@rbac_router.get("/permissions", response_model=schemas.PermissionListStandardResponse)
def get_all_permissions(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    permissions = service.get_permissions(db)
    return {
        "success": True,
        "data": {
            "data": permissions,
            "total": len(permissions),
            "page": 1,
            "limit": len(permissions),
            "total_pages": 1
        },
        "error": None
    }

@rbac_router.put("/roles/{role_id}", response_model=schemas.RoleStandardResponse)
def update_role(role_id: UUID, payload: schemas.RoleCreate, db: Session = Depends(get_db), _ = Depends(require_permission("editar_roles"))):
    try:
        role = service.update_role(db, role_id, payload.name)
        return {"success": True, "data": role, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@rbac_router.delete("/roles/{role_id}", response_model=StandardResponse[None])
def delete_role(role_id: UUID, db: Session = Depends(get_db), _ = Depends(require_permission("eliminar_roles"))):
    try:
        service.delete_role(db, role_id)
        return {"success": True, "data": None, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

