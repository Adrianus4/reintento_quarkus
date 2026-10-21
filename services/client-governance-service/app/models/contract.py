import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class OpenApiContract(Base):
    __tablename__ = "openapi_contracts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_code = Column(String(64), ForeignKey("client_profiles.code", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, default="1.0.0")
    format = Column(String(10), nullable=False, default="json")
    raw_content = Column(Text, nullable=False)
    endpoints_count = Column(Integer, default=0, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = relationship("ClientProfile", back_populates="contracts")

