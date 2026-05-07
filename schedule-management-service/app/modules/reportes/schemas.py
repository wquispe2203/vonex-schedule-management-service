from pydantic import BaseModel, Field
from typing import Optional, List, Generic, TypeVar, Any
from uuid import UUID
from app.core.schemas import StandardResponse, PaginatedResponseData

T = TypeVar("T")

class ReportObservationSchema(BaseModel):
    type: str
    discount_type: str
    has_discount_impact: bool
    replacement_teacher_name: str
    description: str
    ids: List[UUID] = []

class ReportRowResponse(BaseModel):
    id: Any = Field(description="ID puede ser UUID o string para fallbacks")
    fecha_clase: str
    sede: str
    ciclo: str
    docente: str
    curso: str
    hora_inicio: str
    hora_fin: str
    horas_dictadas: float
    receso: float
    is_replacement: bool
    titular_original: Optional[str] = None
    observation: Optional[ReportObservationSchema] = None

class ReportPaginatedData(PaginatedResponseData[ReportRowResponse]):
    total_hours_sum: float
    total_receso_count: float

class ReportFullResponse(StandardResponse[ReportPaginatedData]):
    pass

class SedeListResponse(StandardResponse[PaginatedResponseData[str]]):
    pass

class AulaListResponse(StandardResponse[PaginatedResponseData[str]]):
    pass
