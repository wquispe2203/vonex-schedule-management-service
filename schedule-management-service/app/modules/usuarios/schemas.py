from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.core.schemas import StandardResponse, PaginatedResponseData

class UserBase(BaseModel):
    username: str = Field(..., description="Email institucional (debe terminar en @vonex.edu.pe)")
    nombres: Optional[str] = None
    apellidos: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginPayload(BaseModel):
    username: str
    password: str

# --- ROLES Y PERMISOS ---
class PermissionBase(BaseModel):
    code: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: UUID

    class Config:
        from_attributes = True

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: UUID
    is_protected: bool = False
    created_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True

# Actualizar respuesta del usuario para incluir roles
class UserResponseFull(UserResponse):
    roles: List[RoleResponse] = []

    @computed_field
    @property
    def permissions(self) -> List[str]:
        """Aplanar códigos de permisos de todos los roles para el frontend"""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                if isinstance(perm, str):
                    perms.add(perm)
                else:
                    perms.add(perm.code)
        return sorted(list(perms))

class RoleAssign(BaseModel):
    role_ids: List[UUID]

class PermissionAssign(BaseModel):
    permission_ids: List[UUID]

class PasswordChange(BaseModel):
    new_password: str = Field(..., min_length=6)

# Standardized Responses for Users
class UserStandardResponse(StandardResponse[UserResponseFull]):
    pass

class UserListStandardResponse(StandardResponse[PaginatedResponseData[UserResponseFull]]):
    pass

class RoleStandardResponse(StandardResponse[RoleResponse]):
    pass

class RoleListStandardResponse(StandardResponse[PaginatedResponseData[RoleResponse]]):
    pass

class PermissionListStandardResponse(StandardResponse[PaginatedResponseData[PermissionResponse]]):
    pass
