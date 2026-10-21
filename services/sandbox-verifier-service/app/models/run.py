import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.core.database import Base


class VerificationRun(Base):
    __tablename__ = "verification_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), index=True, nullable=False)
    client_code = Column(String(64), index=True, nullable=False)
    job_id = Column(String(36), index=True, nullable=True)
    status = Column(String(30), default="INITIALIZED", nullable=False)
    compilation_output = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0, nullable=False)
    manifest_json = Column(Text, nullable=True)
    zip_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

