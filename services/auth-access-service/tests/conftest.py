import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.assignment import UserClientAssignment
from app.models.user import User, UserRole

# Use in-memory SQLite for test isolation
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


@pytest.fixture
def admin_user(db_session) -> User:
    user = User(
        email="lead.admin@tcs.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Lead Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(
        subject=admin_user.id,
        email=admin_user.email,
        role=admin_user.role.value
    )


@pytest.fixture
def dev_user(db_session, admin_user: User) -> User:
    user = User(
        email="dev.colleague@tcs.com",
        hashed_password=get_password_hash("DevPass123!"),
        full_name="Dev Colleague",
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Assign client "bcp" to dev
    assignment = UserClientAssignment(
        user_id=user.id,
        client_code="bcp",
        assigned_by_user_id=admin_user.id
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def dev_token(dev_user: User) -> str:
    return create_access_token(
        subject=dev_user.id,
        email=dev_user.email,
        role=dev_user.role.value
    )

