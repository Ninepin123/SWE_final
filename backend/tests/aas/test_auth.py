import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.router import router
from app.modules.aas.security import create_access_token, hash_password


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(engine, tables=[Unit.__table__, User.__table__, AuditLog.__table__])
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def create_user(db_session, *, account="student", password="password123", role="STUDENT", status="ACTIVE"):
    user = User(
        account=account,
        password=hash_password(password),
        name=f"{role} user",
        role=role,
        status=status,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_login_returns_jwt_and_current_user(client, db_session):
    user = create_user(db_session)

    response = client.post(
        "/api/aas/login",
        json={"account": "student", "password": "password123"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["user_id"] == user.user_id
    assert payload["user"]["role"] == "STUDENT"

    me_response = client.get(
        "/api/aas/me",
        headers={"Authorization": f"Bearer {payload['access_token']}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["account"] == "student"


@pytest.mark.parametrize(
    ("account", "password"),
    [
        ("missing", "password123"),
        ("student", "wrong-password"),
    ],
)
def test_login_rejects_invalid_credentials(client, db_session, account, password):
    create_user(db_session)

    response = client.post(
        "/api/aas/login",
        json={"account": account, "password": password},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "帳號或密碼錯誤"


def test_login_rejects_disabled_account(client, db_session):
    create_user(db_session, status="DISABLED")

    response = client.post(
        "/api/aas/login",
        json={"account": "student", "password": "password123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "帳號已停用"


def test_protected_endpoint_rejects_missing_token(client):
    response = client.get("/api/aas/me")

    assert response.status_code in {401, 403}


def test_token_for_disabled_user_is_rejected(client, db_session):
    user = create_user(db_session, status="DISABLED")
    token = create_access_token(user.user_id, user.role)

    response = client.get(
        "/api/aas/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "登入憑證無效或已過期"


def test_logout_requires_valid_token(client, db_session):
    user = create_user(db_session)
    token = create_access_token(user.user_id, user.role)

    response = client.post(
        "/api/aas/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"detail": "已登出"}
