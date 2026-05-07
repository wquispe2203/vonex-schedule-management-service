from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import time
from uuid import UUID
from app.core.schemas import StandardResponse, PaginatedResponseData

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

class ConfigListStandardResponse(StandardResponse[PaginatedResponseData[ConfigResponse]]):
    pass
