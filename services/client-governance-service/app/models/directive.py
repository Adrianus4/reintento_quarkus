import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base


class DirectiveCategory(str, enum.Enum):
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    NAMING = "NAMING"
    TESTING = "TESTING"
    OBSERVABILITY = "OBSERVABILITY"


class DirectiveSeverity(str, enum.Enum):
    MANDATORY = "MANDATORY"
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"


class TechnicalDirective(Base):
    __tablename__ = "technical_directives"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_code = Column(String(64), ForeignKey("client_profiles.code", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(100), nullable=False)
    category = Column(Enum(DirectiveCategory, native_enum=False), nullable=False)
    severity = Column(Enum(DirectiveSeverity, native_enum=False), nullable=False, default=DirectiveSeverity.MANDATORY)
    description = Column(Text, nullable=False)
    deterministic_check = Column(String(255), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    client = relationship("ClientProfile", back_populates="directives")

    __table_args__ = (
        UniqueConstraint("client_code", "rule_code", name="uq_client_rule_code"),
    )

