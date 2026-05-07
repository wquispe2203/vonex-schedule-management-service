from sqlalchemy import Column, Integer, String, Date, Numeric, Time, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from .base import Base

class RptPlanilla(Base):
    __tablename__ = 'rpt_planilla'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    fecha_clase = Column(Date, nullable=False, index=True)
    docente = Column(String(255), nullable=False, index=True)
    sede = Column(String(255), nullable=True)
    ciclo = Column(String(255), nullable=True)
    curso = Column(String(255), nullable=True)
    horas_dictadas = Column(Numeric(10, 2), nullable=False)
    hora_inicio = Column(Time, nullable=True) # Essential for uniqueness
    xml_upload_id = Column(UUID(as_uuid=True), ForeignKey('xml_uploads.id', ondelete='CASCADE'), nullable=True, index=True)
    
    __table_args__ = (
        UniqueConstraint('fecha_clase', 'docente', 'hora_inicio', name='uq_rpt_planilla_unique'),
    )


