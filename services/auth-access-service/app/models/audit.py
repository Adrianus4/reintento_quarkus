import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLoginLog(Base):
    __tablename__ = "audit_login_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    email_attempted = Column(String(255), nullable=False)
    success = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=False, default="unknown")
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="login_logs")

