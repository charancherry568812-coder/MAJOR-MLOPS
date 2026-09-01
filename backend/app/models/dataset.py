"""SQLAlchemy ORM models — Dataset, DatasetVersion, DataQualityReport."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    bank_id = Column(String(36), ForeignKey("banks.id"), nullable=False, index=True)
    description = Column(Text, default="")
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    use_case = Column(String(50), default="credit_risk", index=True)
    status = Column(String(20), default="UPLOADED", index=True)  # UPLOADED,VALIDATING,VALIDATED,PROCESSING,READY,ERROR
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    bank = relationship("Bank", back_populates="datasets")
    versions = relationship("DatasetVersion", back_populates="dataset", order_by="DatasetVersion.created_at.desc()")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    rows = Column(Integer, default=0)
    features = Column(Integer, default=0)
    feature_names = Column(Text, default="[]")  # JSON
    missing_values = Column(Integer, default=0)
    duplicates = Column(Integer, default=0)
    quality_score = Column(Float, default=0.0)
    schema_info = Column(Text, default="{}")  # JSON
    statistics = Column(Text, default="{}")  # JSON
    class_distribution = Column(Text, default="{}")  # JSON
    created_at = Column(DateTime, default=_utcnow)

    dataset = relationship("Dataset", back_populates="versions")
    quality_reports = relationship("DataQualityReport", back_populates="dataset_version")


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    dataset_version_id = Column(String(36), ForeignKey("dataset_versions.id"), nullable=False, index=True)
    missing_value_report = Column(Text, default="{}")  # JSON
    duplicate_report = Column(Text, default="{}")  # JSON
    outlier_report = Column(Text, default="{}")  # JSON
    class_imbalance_report = Column(Text, default="{}")  # JSON
    overall_score = Column(Float, default=0.0)
    recommendations = Column(Text, default="[]")  # JSON
    created_at = Column(DateTime, default=_utcnow)

    dataset_version = relationship("DatasetVersion", back_populates="quality_reports")
