import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, Integer, String
from app.core.database import Base


class GatewayConfig(Base):
    __tablename__ = "gateway_configurations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    active_provider = Column(String(50), default="mock", nullable=False)
    consumption_mode = Column(String(30), default="balanced", nullable=False)
    temperature = Column(Float, default=0.2, nullable=False)
    max_tokens = Column(Integer, default=8192, nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

