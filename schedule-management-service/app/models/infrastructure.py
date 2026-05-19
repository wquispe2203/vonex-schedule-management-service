from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class XmlUpload(Base):
    __tablename__ = 'xml_uploads'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    filename = Column(String(255))
    file_hash = Column(String(64), index=True) # SHA-256 hash for idempotency
    start_date = Column(Date)
    end_date = Column(Date)
    is_force_overwrite = Column(Boolean, default=False)
    status = Column(String(20), default='PENDING') # PENDING, PROCESSING, COMPLETED, FAILED, DEGRADED
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    fallback_count = Column(Integer, default=0)
    process_time_ms = Column(Integer, default=0)
    error_summary = Column(Text, nullable=True)
    storage_path = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    logs = relationship('XmlUploadLog', back_populates='upload')
    change_logs = relationship('XmlChangeLog', back_populates='upload')

class XmlUploadLog(Base):
    __tablename__ = 'xml_upload_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey('xml_uploads.id', ondelete='CASCADE'))
    status = Column(String(50))
    upload = relationship('XmlUpload', back_populates='logs')

class XmlChangeLog(Base):
    __tablename__ = 'xml_change_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey('xml_uploads.id', ondelete='CASCADE'))
    action = Column(String(50))
    upload = relationship('XmlUpload', back_populates='change_logs')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    accion = Column(String(100), nullable=False)
    fecha = Column(DateTime(timezone=True), server_default=func.now())


class RecessRule(Base):
    __tablename__ = 'recess_rules'
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), nullable=False)
    start_time = Column(String(8), nullable=False) # Store as HH:MM:SS or HH:MM
    end_time = Column(String(8), nullable=False)
    deduction_value = Column(Integer, default=33) # Stored in cents (0.33 -> 33) to avoid float issues
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
