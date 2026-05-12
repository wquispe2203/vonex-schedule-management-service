from sqlalchemy import Column, Integer, String, Date, Time, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(100), unique=True, nullable=False)
    classes = relationship("ClassGroup", back_populates="grade")

class Building(Base):
    __tablename__ = "buildings"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    source_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255))
    short_name = Column(String(50))
    lessons = relationship("Lesson", back_populates="subject")

class ClassGroup(Base):
    __tablename__ = "classes"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    source_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100))
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id", ondelete="SET NULL"))
    grade = relationship("Grade", back_populates="classes")
    lessons = relationship("Lesson", back_populates="class_group")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    source_id = Column(String(50), unique=True, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"))
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"))
    legacy_subject_id = Column(Integer, index=True)
    legacy_teacher_id = Column(Integer, index=True)
    legacy_class_id = Column(Integer, index=True)
    subject = relationship("Subject", back_populates="lessons")
    teacher = relationship("Teacher", back_populates="lessons")
    class_group = relationship("ClassGroup", back_populates="lessons")
    sessions = relationship("ScheduleSession", back_populates="lesson")
    cards = relationship("Card", back_populates="lesson")

class Card(Base):
    __tablename__ = "cards"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    source_id = Column(String(50), unique=True, nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    days = Column(String(10))
    period = Column(Integer)
    lesson = relationship("Lesson", back_populates="cards")

class ScheduleSession(Base):
    __tablename__ = "schedule_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id", ondelete="CASCADE"))
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(50), default="ACTIVE")
    xml_upload_id = Column(UUID(as_uuid=True), ForeignKey('xml_uploads.id', ondelete='CASCADE'), nullable=True, index=True)
    __table_args__ = (
        UniqueConstraint('lesson_id', 'session_date', 'start_time', name='uq_session_lesson_time'),
    )
    lesson = relationship("Lesson", back_populates="sessions")
    observations = relationship("Observation", back_populates="session")

class Observation(Base):
    __tablename__ = "observations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    legacy_id = Column(Integer, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("schedule_sessions.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    replacement_teacher_id = Column(UUID(as_uuid=True), ForeignKey("teachers.id", ondelete="SET NULL"))
    legacy_session_id = Column(Integer, index=True)
    legacy_teacher_id = Column(Integer, index=True)
    type = Column(String(50), nullable=False)
    discount_type = Column(String(50), default="SIMPLE")
    replacement_teacher_name = Column(String(255))
    teacher_uid = Column(UUID(as_uuid=True), nullable=True)
    replacement_teacher_uid = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ScheduleSession", back_populates="observations")
    user = relationship("User", back_populates="observations")
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    replacement_teacher = relationship("Teacher", foreign_keys=[replacement_teacher_id])
