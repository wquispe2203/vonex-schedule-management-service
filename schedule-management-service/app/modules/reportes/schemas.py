from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic, Union, Any
from datetime import date, time
from uuid import UUID

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] | T

class ReportObservationSchema(BaseModel):
    type: str
    discount_type: str
    has_discount_impact: bool
    replacement_teacher_name: str
    description: str
    ids: List[UUID] = []

class ReportRowResponse(BaseModel):
    id: UUID
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

class ReportFullResponse(BaseModel):
    success: bool
    data: List[ReportRowResponse]
    total_records: int
    total_pages: int
    current_page: int
    total_hours_sum: float
    total_receso_count: float
