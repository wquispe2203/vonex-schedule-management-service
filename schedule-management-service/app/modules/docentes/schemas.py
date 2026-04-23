from typing import List, TypeVar, Generic, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T]


# ─── Teachers Maestra ────────────────────────────────────

class TeacherOut(BaseModel):
    id: UUID
    source_id: Optional[str] = None
    first_name: str
    last_name: str
    short_name: str
    dni: Optional[str] = None
    razon_social: Optional[str] = None
    normalized_name: str
    is_active: Optional[bool] = None
    is_assigned: Optional[bool] = True
    possible_duplicate: Optional[bool] = False

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


# ─── Teachers Sin Asignar ────────────────────────────────

class SinAsignarOut(BaseModel):
    id: UUID
    dni: str
    apellidos: str
    nombres: str
    razon_social: str
    normalized_name: str
    last_seen_at: Optional[str] = ""

    class Config:
        from_attributes = True


class SinAsignarUpdate(BaseModel):
    dni: Optional[str] = None
    apellidos: Optional[str] = None
    nombres: Optional[str] = None
    razon_social: Optional[str] = None


# ─── Excel Import ────────────────────────────────────────

class ExcelImportResult(BaseModel):
    success: bool
    inserted: int
    updated: int
    skipped: int
    rows: List[Dict[str, Any]]


# ─── XML Cross-check ─────────────────────────────────────

class XmlCrossCheckResult(BaseModel):
    success: bool
    nuevos_sinasignar: int
    ya_en_maestra: int
    ya_en_sinasignar: int
    detalle_nuevos: List[str]


# ─── Generic paged response ──────────────────────────────

class PagedResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T]
    total: int
    page: int
    total_pages: int

# ─── MDM Review ──────────────────────────────────────────

class MatchReviewOut(BaseModel):
    id: UUID
    xml_raw_name: str
    normalized_name: str
    candidate_id: UUID
    score: float
    decision: str
    request_id: Optional[UUID] = None
    xml_source_id: Optional[str] = None
    status: str
    
    # Auditoría v4
    resolved_by: Optional[UUID] = None
    resolved_by_snapshot: Optional[str] = None
    resolved_at: Optional[Any] = None
    resolution_note: Optional[str] = None
    resolution_time_seconds: Optional[int] = None
    resolution_type: Optional[str] = None
    
    created_at: Any
    
    candidate: Optional[TeacherOut] = None

    class Config:
        from_attributes = True


class MdmStatsOut(BaseModel):
    total_reviews: int
    pending: int
    resolved: int
    rejected: int
    percentage_manual: float
    percentage_dudosos: float
    avg_resolution_time_minutes: float
    alert_quality: bool
    data_points: List[Dict[str, Any]] # Para gráficas
