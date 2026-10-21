import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.DEVELOPER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    client_assignments = relationship(
        "UserClientAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="UserClientAssignment.user_id"
    )
    login_logs = relationship(
        "AuditLoginLog",
        back_populates="user",
        cascade="all, delete-orphan"
    )

