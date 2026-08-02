import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app

# In-memory SQLite using StaticPool so all threads share the same database tables
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_and_login_flow():
    # 1. Register new user
    register_payload = {
        "email": "qa_user@example.com",
        "password": "SecurePassword123!",
        "company_name": "QA Testing Inc",
    }
    res_reg = client.post("/api/v1/auth/register", json=register_payload)
    assert res_reg.status_code == 201
    assert res_reg.json()["email"] == "qa_user@example.com"

    # 2. Duplicate registration attempt should return 400
    res_dup = client.post("/api/v1/auth/register", json=register_payload)
    assert res_dup.status_code == 400

    # 3. Login
    login_payload = {
        "username": "qa_user@example.com",
        "password": "SecurePassword123!",
    }
    res_login = client.post("/api/v1/auth/login", data=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_unauthorized_access():
    res = client.get("/api/v1/workflows")
    assert res.status_code == 401
