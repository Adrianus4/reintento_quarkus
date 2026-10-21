import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    package_prefix = Column(String(255), nullable=False, default="com.tcs.generated")
    java_version = Column(String(10), nullable=False, default="17")
    quarkus_version = Column(String(20), nullable=False, default="3.15.1")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    directives = relationship(
        "TechnicalDirective",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    contracts = relationship(
        "OpenApiContract",
        back_populates="client",
        cascade="all, delete-orphan"
    )

