from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from . import schemas, service
from app.dependencies.auth import get_current_user, require_permission
from typing import List

router = APIRouter(prefix="/api/users", tags=["Usuarios"])
rbac_router = APIRouter(prefix="/api/rbac", tags=["RBAC"])

@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginPayload, db: Session = Depends(get_db)):
    try:
        return service.authenticate_user(db, payload.username, payload.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me", response_model=schemas.UserResponseFull)
def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.get("", response_model=List[schemas.UserResponseFull])
def list_users(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_users(db)

@router.post("", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Nota: Aquí habitualmente también se requeriría permiso, pero por demo permitimos crear el primer admin
    try:
        return service.create_user(db, user_data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user_info(user_id: int, user_data: schemas.UserBase, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.update_user(db, user_id, user_data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.patch("/{user_id}/password", response_model=schemas.UserResponse)
def change_password(user_id: int, payload: schemas.PasswordChange, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.update_user_password(db, user_id, payload.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{user_id}", response_model=schemas.UserResponse)
def remove_user(user_id: int, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.delete_user(db, user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{user_id}/roles", response_model=schemas.UserResponseFull)
def assign_roles(user_id: int, payload: schemas.RoleAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.assign_roles_to_user(db, user_id, payload.role_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS ROLES (RBAC) ---
@rbac_router.get("/roles", response_model=List[schemas.RoleResponse])
def get_all_roles(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_roles(db)

@rbac_router.post("/roles", response_model=schemas.RoleResponse)
def create_new_role(role_data: schemas.RoleCreate, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.create_role(db, role_data.name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@rbac_router.post("/roles/{role_id}/permissions", response_model=schemas.RoleResponse)
def assign_permissions(role_id: int, payload: schemas.PermissionAssign, db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    try:
        return service.assign_permissions_to_role(db, role_id, payload.permission_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- ENDPOINTS PERMISOS (RBAC) ---
@rbac_router.get("/permissions", response_model=List[schemas.PermissionResponse])
def get_all_permissions(db: Session = Depends(get_db), _ = Depends(require_permission("gestionar_usuarios"))):
    return service.get_permissions(db)
