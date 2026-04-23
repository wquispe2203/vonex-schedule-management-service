from pydantic import BaseModel, ConfigDict
from typing import Optional, List, TypeVar, Generic, Union
from datetime import time
from uuid import UUID

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[Union[T, List[T]]] = None
    message: Optional[str] = None

class ConfigSchema(BaseModel):
    description: Optional[str] = None
    start_time: str # El frontend envía "HH:MM"
    end_time: str

class ConfigResponse(BaseModel):
    id: UUID
    description: Optional[str] = None
    start_time: time
    end_time: time

    model_config = ConfigDict(from_attributes=True)
