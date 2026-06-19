"""AAS015-016 — 系統維運監控（線上人數 / 負載 / 計數 / 異常警示）。"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.monitoring import metrics
from app.modules.aas.router import router
from app.modules.aas.security import create_access_token, hash_password


@pytest.fixture(autouse=True)
def _reset_metrics():
    metrics.reset()
    yield
    metrics.reset()


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


def mk_user(db, account, *, role="STUDENT"):
    u = User(account=account, password=hash_password("password123"), name=account, role=role, status="ACTIVE")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def login(client, account, password="password123"):
    r = client.post("/api/aas/login", json={"account": account, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_metrics_report_online_users_counts_and_load(client, db_session):
    mk_user(db_session, "admin", role="ADMIN")
    mk_user(db_session, "stu1")
    mk_user(db_session, "stu2")

    admin_token = login(client, "admin")  # 3 個帳號全部登入 → 3 個有效 session
    login(client, "stu1")
    login(client, "stu2")

    # 模擬流量（中介層在實際部署收集；測試直接打點以求確定性）
    for _ in range(10):
        metrics.record_request(200)
    for _ in range(2):
        metrics.record_request(500)

    r = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    data = r.json()

    assert data["online_users"] == 3
    assert data["total_users"] == 3
    assert data["requests_total"] == 12
    assert data["errors_total"] == 2
    assert data["error_rate"] == round(2 / 12, 4)
    # psutil 已安裝 → 應有伺服器負載
    assert data["server_load"] is not None
    assert "cpu_percent" in data["server_load"]
    assert "memory_percent" in data["server_load"]
    # 12 筆 < 門檻樣本數 20，且失敗為 0 → 無警示
    assert data["alerts"] == []


def test_online_users_drops_after_logout(client, db_session):
    mk_user(db_session, "admin", role="ADMIN")
    mk_user(db_session, "stu1")
    admin_token = login(client, "admin")
    stu_token = login(client, "stu1")

    before = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert before["online_users"] == 2

    client.post("/api/aas/logout", headers={"Authorization": f"Bearer {stu_token}"})

    after = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert after["online_users"] == 1


def test_non_admin_cannot_view_metrics(client, db_session):
    student = mk_user(db_session, "stu1")
    token = create_access_token(student.user_id, student.role)  # 無 session 的直接 token
    r = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_login_failure_spike_triggers_alert(client, db_session):
    mk_user(db_session, "admin", role="ADMIN")

    for _ in range(5):
        bad = client.post("/api/aas/login", json={"account": "admin", "password": "wrong"})
        assert bad.status_code == 401

    admin_token = login(client, "admin")
    data = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {admin_token}"}).json()

    assert data["login_failures_total"] == 5
    codes = {a["code"] for a in data["alerts"]}
    assert "LOGIN_FAILURE_SPIKE" in codes


def test_high_error_rate_triggers_alert(client, db_session):
    mk_user(db_session, "admin", role="ADMIN")
    admin_token = login(client, "admin")

    for _ in range(10):
        metrics.record_request(200)
    for _ in range(10):
        metrics.record_request(500)  # 20 筆、50% 錯誤率

    data = client.get("/api/aas/monitoring/metrics", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert data["error_rate"] == 0.5
    alerts = {a["code"]: a["level"] for a in data["alerts"]}
    assert alerts.get("HIGH_ERROR_RATE") == "CRITICAL"
