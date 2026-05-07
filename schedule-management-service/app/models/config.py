from sqlalchemy import Column, String, Time
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class BreakConfig(Base):
    __tablename__ = 'break_config'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    description = Column(String(255), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

class LunchConfig(Base):
    __tablename__ = 'lunch_config'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    description = Column(String(255), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

