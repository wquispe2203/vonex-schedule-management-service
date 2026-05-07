from typing import List, TypeVar, Generic, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.core.schemas import StandardResponse, PaginatedResponseData

T = TypeVar("T")

class TeacherHoursItem(BaseModel):
    teacher_id: UUID
    name: str
    dni: str
    total_hours: float

    model_config = ConfigDict(from_attributes=True)

# ─── Teachers Maestra ────────────────────────────────────

class TeacherOut(BaseModel):
    id: UUID
    source_id: Optional[str] = None
    nombres: str
    apellidos: str
    short_name: str
    dni: Optional[str] = None
    razon_social: Optional[str] = None
    normalized_name: str
    is_active: Optional[bool] = None
    is_assigned: Optional[bool] = True
    status: str = "ACTIVO"
    possible_duplicate: Optional[bool] = False

    model_config = ConfigDict(from_attributes=True)

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
    id: Optional[UUID] = None
    dni: Optional[str] = None
    apellidos: Optional[str] = None
    nombres: Optional[str] = None
    razon_social: Optional[str] = None
    normalized_name: Optional[str] = None
    status: str = "INCOMPLETO"
    last_seen_at: Optional[str] = ""
    nombre_xml: Optional[str] = None
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SinAsignarUpdate(BaseModel):
    dni: Optional[str] = None
    apellidos: Optional[str] = None
    nombres: Optional[str] = None
    razon_social: Optional[str] = None

# ─── Excel Import ────────────────────────────────────────

class ExcelRowDetail(BaseModel):
    fila: int
    dni: str
    apellidos: str
    nombres: str
    razon_social: str
    estado: str # INSERTADO | ACTUALIZADO | ERROR
    mensaje: Optional[str] = None

class ExcelImportResult(BaseModel):
    inserted: int
    updated: int
    skipped: int
    rows: List[ExcelRowDetail]

# ─── XML Cross-check ─────────────────────────────────────

class XmlCrossCheckResult(BaseModel):
    nuevos_sinasignar: int
    ya_en_maestra: int
    ya_en_sinasignar: int
    detalle_nuevos: List[str]

class ConflictCandidate(BaseModel):
    teacher_id: str
    name: str
    dni: Optional[str] = None
    score: float

class ConflictoDocenteOut(BaseModel):
    nombre_xml: str
    motivo: str
    posibles_coincidencias: List[ConflictCandidate]
    similitud: float

    model_config = ConfigDict(from_attributes=True)

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
    resolved_by: Optional[UUID] = None
    resolved_by_snapshot: Optional[str] = None
    resolved_at: Optional[Any] = None
    resolution_note: Optional[str] = None
    resolution_time_seconds: Optional[int] = None
    resolution_type: Optional[str] = None
    created_at: Any
    candidate: Optional[TeacherOut] = None

    model_config = ConfigDict(from_attributes=True)

class MdmStatsOut(BaseModel):
    total_reviews: int
    pending: int
    resolved: int
    rejected: int
    percentage_manual: float
    percentage_dudosos: float
    avg_resolution_time_minutes: float
    alert_quality: bool
    data_points: List[Dict[str, Any]]

class ExcelImportPaginatedData(PaginatedResponseData[ExcelRowDetail]):
    inserted: int
    updated: int
    skipped: int

# --- Standardized Responses ---
class DocenteStandardResponse(StandardResponse[TeacherOut]):
    pass

class DocenteListStandardResponse(StandardResponse[PaginatedResponseData[TeacherOut]]):
    pass

class SinAsignarListStandardResponse(StandardResponse[PaginatedResponseData[SinAsignarOut]]):
    pass

class MatchReviewListStandardResponse(StandardResponse[PaginatedResponseData[MatchReviewOut]]):
    pass

class ExcelImportStandardResponse(StandardResponse[ExcelImportPaginatedData]):
    pass

class ConflictoListStandardResponse(StandardResponse[PaginatedResponseData[ConflictoDocenteOut]]):
    pass

class ResolveConflictRequest(BaseModel):
    xml_name_raw: str
    teacher_id: UUID
    is_global: bool = False

class ResolveConflictResponse(BaseModel):
    override_id: UUID
    message: str

