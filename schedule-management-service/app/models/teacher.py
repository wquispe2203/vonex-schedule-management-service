from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    source_id = Column(String(50), unique=True, nullable=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    dni = Column(String(15), nullable=True)
    short_name = Column(String(50), nullable=True)
    razon_social = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="ACTIVO", index=True) # ACTIVO, INCOMPLETO, CONFLICTO, INVALIDO
    normalized_name = Column(String(400), nullable=True, index=True)
    possible_duplicate = Column(Boolean, default=False)
    
    is_assigned = Column(Boolean, default=True, index=True)
    times_detected = Column(Integer, default=0)
    last_seen_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True)
    source = Column(String(100))
    possible_match_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"))
    match_review_id = Column(UUID(as_uuid=True), ForeignKey("match_reviews.id", ondelete="SET NULL"))
    merged_into_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    normalized_for_match = Column(String(400), nullable=True, index=True)
    
    lessons = relationship("Lesson", back_populates="teacher")
    possible_match = relationship("Teacher", remote_side=[id], foreign_keys=[possible_match_id])
    review = relationship("MatchReview", foreign_keys=[match_review_id])

class MatchReview(Base):
    __tablename__ = "match_reviews"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    xml_raw_name = Column(String(255), nullable=False)
    normalized_name = Column(String(400), nullable=False)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    xml_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    score = Column(Numeric(5, 2))
    decision = Column(String(50), default="MATCH_DUDOSO")
    request_id = Column(UUID(as_uuid=True), nullable=True)
    xml_source_id = Column(String(100), nullable=True)
    upload_id = Column(UUID(as_uuid=True), ForeignKey("xml_uploads.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="PENDING")
    
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_by_snapshot = Column(String(255), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    resolution_time_seconds = Column(Integer, nullable=True)
    resolution_type = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    candidate = relationship("Teacher", foreign_keys=[candidate_id])
    xml_teacher = relationship("Teacher", foreign_keys=[xml_teacher_id])
    resolver = relationship("User", foreign_keys=[resolved_by])

class TeacherNameOverride(Base):
    __tablename__ = "teacher_name_overrides"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    xml_name_raw = Column(String(255), nullable=False)
    xml_name_normalized = Column(String(400), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    xml_upload_id = Column(UUID(as_uuid=True), ForeignKey("xml_uploads.id", ondelete="CASCADE"), nullable=True)
    confidence = Column(Numeric(5, 2), default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
