from pydantic import BaseModel, field_validator
from typing import Optional, List, TypeVar, Generic, Union, Any
from uuid import UUID
from datetime import date

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] | T

# Entradas (Requests) con validación restaurada
class ObservationPayload(BaseModel):
    session_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    replacement_teacher_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    type: Optional[str] = "FALTA"
    discount_type: Optional[str] = "SIMPLE"
    replacement_teacher_name: Optional[str] = None
    replacement_last_name: Optional[str] = None
    replacement_first_name: Optional[str] = None
    description: Optional[str] = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# Salidas (Responses)
class ObservationResponse(BaseModel):
    id: UUID
    session_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    type: Optional[str] = None
    discount_type: Optional[str] = None
    replacement_teacher_name: Optional[str] = None
    replacement_teacher_id: Optional[UUID] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

class ObservationLogResponse(BaseModel):
    id: UUID
    date_record: Optional[str] = None
    user: Optional[str] = None
    teacher_affected: Optional[str] = None
    type: Optional[str] = None
    replacement_teacher_name: Optional[str] = None
    class_date: Optional[str] = None
    description: Optional[str] = None

