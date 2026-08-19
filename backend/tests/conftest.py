import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.entities import Base, User
from backend.app.core.security import get_password_hash

# Create single static in-memory engine for test suite
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def setup_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def reset_db_data():
    db = TestingSessionLocal()
    # Clear tables before each test
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()

    # Seed default test users
    admin = User(
        username="admin",
        email="admin@peblo.tv",
        hashed_password=get_password_hash("admin123"),
        role="admin",
        is_active=True
    )
    editor = User(
        username="editor",
        email="editor@peblo.tv",
        hashed_password=get_password_hash("editor123"),
        role="editor",
        is_active=True
    )
    db.add_all([admin, editor])
    db.commit()
    db.close()
    yield

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers(client):
    resp = client.post("/api/v1/auth/login", json={"username": "editor", "password": "editor123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
