import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserClientAssignment(Base):
    __tablename__ = "user_client_assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_code = Column(String(64), nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    assigned_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="client_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_user_id])

    __table_args__ = (
        UniqueConstraint("user_id", "client_code", name="uq_user_client_code"),
    )

