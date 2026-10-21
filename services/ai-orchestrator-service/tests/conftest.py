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

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import Base
from app.main import app

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

