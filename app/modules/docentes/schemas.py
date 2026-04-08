from pydantic import BaseModel
from typing import List, TypeVar, Generic, Optional, Any, Dict

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T]

class TeacherOut(BaseModel):
    id: int
    source_id: str
    first_name: str
    last_name: str
    short_name: str
    dni: str
    razon_social: str
    normalized_name: str
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True

class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    short_name: Optional[str] = ""
    dni: Optional[str] = None
    razon_social: Optional[str] = None

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    short_name: Optional[str] = None
    dni: Optional[str] = None
    razon_social: Optional[str] = None

class SinAsignarOut(BaseModel):
    id: int
    dni: str
    apellidos: str
    nombres: str
    razon_social: str
    normalized_name: str
    created_at: str

    class Config:
        from_attributes = True

class SinAsignarUpdate(BaseModel):
    dni: Optional[str] = None
    apellidos: Optional[str] = None
    nombres: Optional[str] = None
    razon_social: Optional[str] = None

class ExcelImportResult(BaseModel):
    success: bool
    inserted: int
    updated: int
    skipped: int
    rows: List[Dict[str, Any]]

class PagedResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T]
    total: int
    page: int
    total_pages: int
