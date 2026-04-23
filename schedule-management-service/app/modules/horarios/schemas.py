from pydantic import BaseModel, computed_field
from typing import Optional, List, TypeVar, Generic
from uuid import UUID

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: List[T] | T

class TeacherBasicResponse(BaseModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]

    @computed_field
    @property
    def uid(self) -> str:
        return str(self.id)

    class Config:
        from_attributes = True

class ClassGroupResponse(BaseModel):
    id: UUID
    name: Optional[str]

class ObservationSubResponse(BaseModel):
    id: UUID
    type: str
    start_time: Optional[str]
    end_time: Optional[str]

class TeacherSessionResponse(BaseModel):
    id: Optional[UUID]
    rpt_id: Optional[UUID] = None
    date: str
    start_time: str
    end_time: str
    subject: str
    class_group: str
    sede: str
    horas_dictadas: float
    receso: float = 0.0
    is_break: bool
    status: str
    is_virtual: bool
    is_replacement: bool = False
    titular_name: Optional[str] = None
    observations: List[ObservationSubResponse]

class ClassroomSessionResponse(BaseModel):
    id: UUID
    date: str
    start_time: str
    end_time: str
    subject: Optional[str]
    teacher: Optional[str]
    is_break: bool
    status: str
    observations: List[ObservationSubResponse]
