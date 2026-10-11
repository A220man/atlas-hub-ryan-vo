import datetime
import uuid
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class Presentation(Base):
    __tablename__ = "presentations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    topic = Column(String(255), nullable=True)
    raw_content = Column(Text, nullable=False)
    template_id = Column(String(64), default="modern-navy", nullable=False)
    status = Column(String(32), default="draft", nullable=False, index=True)
    aspect_ratio = Column(String(16), default="16:9", nullable=False)
    created_by = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    slides = relationship("Slide", back_populates="presentation", cascade="all, delete-orphan", order_by="Slide.slide_index")
    evaluations = relationship("EvaluationReport", back_populates="presentation", cascade="all, delete-orphan")
    narration_plans = relationship("NarrationPlan", back_populates="presentation", cascade="all, delete-orphan")


class Slide(Base):
    __tablename__ = "slides"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    presentation_id = Column(String(36), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    slide_index = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    layout_type = Column(String(64), nullable=False)
    content_json = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    presentation = relationship("Presentation", back_populates="slides")

    __table_args__ = (
        Index("ix_slide_pres_index", "presentation_id", "slide_index"),
    )


class EvaluationReport(Base):
    __tablename__ = "evaluation_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    presentation_id = Column(String(36), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    overall_score = Column(Float, nullable=False)
    grounding_score = Column(Float, nullable=False)
    balance_score = Column(Float, nullable=False)
    pacing_score = Column(Float, nullable=False)
    consistency_score = Column(Float, nullable=False)
    status = Column(String(32), default="completed", nullable=False)
    diagnostics_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    presentation = relationship("Presentation", back_populates="evaluations")


class NarrationPlan(Base):
    __tablename__ = "narration_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    presentation_id = Column(String(36), ForeignKey("presentations.id", ondelete="CASCADE"), nullable=False, index=True)
    total_duration_seconds = Column(Float, nullable=False)
    estimated_words = Column(Integer, nullable=False)
    voice_id = Column(String(64), default="neutral-presenter", nullable=False)
    target_wpm = Column(Integer, default=140, nullable=False)
    cues_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    presentation = relationship("Presentation", back_populates="narration_plans")


class CustomTemplate(Base):
    __tablename__ = "custom_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=False)
    description = Column(String(255), nullable=True)
    filename = Column(String(255), nullable=False)
    content_b64 = Column(Text, nullable=False)
    layout_count = Column(Integer, default=0, nullable=False)
    aspect_ratio = Column(String(16), default="16:9", nullable=False)
    uploaded_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(128), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False, index=True)
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
