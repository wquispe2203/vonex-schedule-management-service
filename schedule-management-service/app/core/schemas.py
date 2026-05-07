from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Any, Generic, TypeVar, List
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

class PaginatedResponseData(BaseModel, Generic[T]):
    """Contrato intermedio para cumplir con response.data.data en Pydantic v2."""
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)

class StandardResponse(BaseModel, Generic[T]):
    """Contrato global de respuesta tipado."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode='after')
    def validate_pagination_integrity(self) -> 'StandardResponse':
        if isinstance(self.data, list):
            # No bloqueamos pero registramos el error para auditoría de contrato
            logger.error(
                "DEFENSIVE_VALIDATION: Se detectó una lista directa en 'data'. "
                "Para coherencia del sistema, use PaginatedResponseData."
            )
        return self
