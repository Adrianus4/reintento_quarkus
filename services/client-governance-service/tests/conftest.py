import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from datetime import datetime, timedelta, timezone
from typing import Dict, List
import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app
from app.models.client import ClientProfile

# In-memory SQLite for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _generate_test_token(role: str, user_id: str, assigned_clients: List[str]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": f"{user_id}@tcs.com",
        "role": role,
        "assigned_clients": assigned_clients,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def admin_headers() -> Dict[str, str]:
    token = _generate_test_token("ADMIN", "admin-user", ["*"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def bcp_dev_headers() -> Dict[str, str]:
    token = _generate_test_token("DEVELOPER", "dev-bcp", ["bcp"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def retail_dev_headers() -> Dict[str, str]:
    token = _generate_test_token("DEVELOPER", "dev-retail", ["retail-corp"])
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_bcp_client(db_session) -> ClientProfile:
    client_obj = ClientProfile(
        code="bcp",
        name="Banco de Credito del Peru",
        description="Banking account with high resilience standards",
        package_prefix="com.bcp.enterprise",
        java_version="17",
        quarkus_version="3.15.1",
        is_active=True,
    )
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(client_obj)
    return client_obj


@pytest.fixture
def sample_retail_client(db_session) -> ClientProfile:
    client_obj = ClientProfile(
        code="retail-corp",
        name="Global Retail Corp",
        description="Retail e-commerce microservices",
        package_prefix="com.retail.services",
        java_version="21",
        quarkus_version="3.15.1",
        is_active=True,
    )
    db_session.add(client_obj)
    db_session.commit()
    db_session.refresh(client_obj)
    return client_obj
