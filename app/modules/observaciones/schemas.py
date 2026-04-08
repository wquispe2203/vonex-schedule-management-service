from pydantic import BaseModel
from typing import Optional, List, TypeVar, Generic

T = TypeVar('T')

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[List[T] | T]

class ObservationPayload(BaseModel):
    session_id: int
    teacher_id: int
    type: str
    discount_type: Optional[str] = "SIMPLE"
    replacement_teacher_name: Optional[str] = None
    replacement_teacher_id: Optional[int] = None
    description: Optional[str] = ""

class ObservationResponse(BaseModel):
    id: int
    session_id: int
    teacher_id: int
    type: str
    discount_type: str
    replacement_teacher_name: Optional[str] = None
    replacement_teacher_id: Optional[int] = None
    description: str
    created_at: str

class ObservationLogResponse(BaseModel):
    id: int
    action: str
    details: str
    created_at: str
