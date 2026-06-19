"""AAS003 — 防止同帳號異地重複登入（單一登入 / session 輪替）。"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.security import create_access_token, hash_password
from app.modules.aas.router import router


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


def create_user(db_session, *, account="alice", password="password123", role="STUDENT"):
    user = User(account=account, password=hash_password(password), name=account, role=role, status="ACTIVE")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login(client, account="alice", password="password123"):
    r = client.post("/api/aas/login", json={"account": account, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_relogin_invalidates_previous_session_token(client, db_session):
    create_user(db_session)

    token1 = login(client)
    assert client.get("/api/aas/me", headers={"Authorization": f"Bearer {token1}"}).status_code == 200

    # 第二次登入（模擬異地登入）會輪替 session
    token2 = login(client)

    # 舊 token 立即失效
    r_old = client.get("/api/aas/me", headers={"Authorization": f"Bearer {token1}"})
    assert r_old.status_code == 401
    assert r_old.json()["detail"] == "帳號已在其他裝置登入，此連線已失效"

    # 新 token 仍有效
    assert client.get("/api/aas/me", headers={"Authorization": f"Bearer {token2}"}).status_code == 200


def test_logout_invalidates_token(client, db_session):
    create_user(db_session)
    token = login(client)

    assert client.post("/api/aas/logout", headers={"Authorization": f"Bearer {token}"}).status_code == 200

    # 登出後同一 token 不可再用
    r = client.get("/api/aas/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_login_sets_session_token_on_user(client, db_session):
    user = create_user(db_session)
    assert user.session_token is None

    login(client)
    db_session.refresh(user)
    assert user.session_token is not None
    assert user.session_expires_at is not None


def test_plain_token_without_jti_is_backward_compatible(client, db_session):
    """未經 login 直接簽發、且帳號無 active session 的 token 仍可使用（向後相容）。"""
    user = create_user(db_session)
    token = create_access_token(user.user_id, user.role)  # 無 jti
    assert client.get("/api/aas/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
