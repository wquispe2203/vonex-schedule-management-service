from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.dependencies.auth import require_permission
from . import schemas, service

router = APIRouter(prefix="/api/users", tags=["Users & Security"])
rbac_router = APIRouter(prefix="/api", tags=["Roles & Permissions"])

@router.post("", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.create_user(db, user_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor")

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

# --- ENDPOINTS USUARIOS ---
from typing import List
from app.models import User
from app.dependencies.auth import get_current_user

@router.get("/me", response_model=schemas.UserResponseFull)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("", response_model=List[schemas.UserResponseFull])
def get_all_users(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_users(db)

@router.put("/{user_id}", response_model=schemas.UserResponseFull)
def update_user(user_id: UUID, user_data: schemas.UserBase, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.update_user(db, user_id, user_data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/password")
def change_password(user_id: UUID, payload: schemas.PasswordChange, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        service.update_user_password(db, user_id, payload.new_password)
        return {"success": True, "message": "Password actualizada correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}", response_model=schemas.UserResponseFull)
def deactivate_user(user_id: UUID, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.delete_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_id}/roles", response_model=schemas.UserResponseFull)
def assign_roles(user_id: UUID, payload: schemas.RoleAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.assign_roles_to_user(db, user_id, payload.role_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS ROLES (RBAC) ---
@rbac_router.get("/roles", response_model=List[schemas.RoleResponse])
def get_all_roles(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_roles(db)

@rbac_router.post("/roles", response_model=schemas.RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(payload: schemas.RoleCreate, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.create_role(db, payload.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@rbac_router.post("/roles/{role_id}/permissions", response_model=schemas.RoleResponse)
def assign_permissions(role_id: UUID, payload: schemas.PermissionAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.assign_permissions_to_role(db, role_id, payload.permission_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS PERMISOS (RBAC) ---
@rbac_router.get("/permissions", response_model=List[schemas.PermissionResponse])
def get_all_permissions(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_permissions(db)

