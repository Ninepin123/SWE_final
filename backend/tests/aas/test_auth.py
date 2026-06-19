import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.router import router
from app.modules.aas.security import create_access_token, hash_password, verify_password


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


def auth_headers(user):
    token = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_update_search_and_delete_user(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")

    create_response = client.post(
        "/api/aas/users",
        headers=auth_headers(admin),
        json={
            "account": "teacher01",
            "password": "initial-pass",
            "name": "王老師",
            "role": "TEACHER",
            "email": "teacher01@nuk.edu.tw",
            "department": "資訊工程學系",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    user_id = created["user_id"]
    stored = db_session.get(User, user_id)
    assert stored.password != "initial-pass"
    assert verify_password("initial-pass", stored.password)

    search_response = client.get(
        "/api/aas/users",
        headers=auth_headers(admin),
        params={"keyword": "王老師", "role": "TEACHER", "account_status": "ACTIVE"},
    )
    assert search_response.status_code == 200
    assert [item["user_id"] for item in search_response.json()] == [user_id]

    update_response = client.put(
        f"/api/aas/users/{user_id}",
        headers=auth_headers(admin),
        json={
            "name": "王教授",
            "status": "DISABLED",
            "password": "updated-pass",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "王教授"
    assert update_response.json()["status"] == "DISABLED"
    db_session.refresh(stored)
    assert verify_password("updated-pass", stored.password)

    delete_response = client.delete(
        f"/api/aas/users/{user_id}",
        headers=auth_headers(admin),
    )
    assert delete_response.status_code == 200
    assert db_session.get(User, user_id) is None

    actions = list(db_session.scalars(select(AuditLog.action).order_by(AuditLog.log_id)))
    assert actions == ["CREATE_USER", "UPDATE_USER", "DELETE_USER"]


def test_non_admin_cannot_manage_users(client, db_session):
    student = create_user(db_session)

    response = client.get("/api/aas/users", headers=auth_headers(student))

    assert response.status_code == 403
    assert response.json()["detail"] == "權限不足"


def test_duplicate_account_is_rejected(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")
    create_user(db_session, account="duplicate")

    response = client.post(
        "/api/aas/users",
        headers=auth_headers(admin),
        json={
            "account": "duplicate",
            "password": "password123",
            "name": "重複帳號",
            "role": "STUDENT",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "帳號已存在"


def test_admin_cannot_disable_or_delete_self(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")
    headers = auth_headers(admin)

    disable_response = client.put(
        f"/api/aas/users/{admin.user_id}",
        headers=headers,
        json={"status": "DISABLED"},
    )
    delete_response = client.delete(
        f"/api/aas/users/{admin.user_id}",
        headers=headers,
    )

    assert disable_response.status_code == 400
    assert disable_response.json()["detail"] == "不能停用目前登入的管理員帳號"
    assert delete_response.status_code == 400
    assert delete_response.json()["detail"] == "不能刪除目前登入的管理員帳號"
    db_session.refresh(admin)
    assert admin.status == "ACTIVE"


def test_user_search_validates_role_and_status(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")

    role_response = client.get(
        "/api/aas/users",
        headers=auth_headers(admin),
        params={"role": "UNKNOWN"},
    )
    status_response = client.get(
        "/api/aas/users",
        headers=auth_headers(admin),
        params={"account_status": "UNKNOWN"},
    )

    assert role_response.status_code == 400
    assert role_response.json()["detail"] == "角色不存在"
    assert status_response.status_code == 400
    assert status_response.json()["detail"] == "狀態不存在"


def test_login_and_logout_are_written_to_audit_log(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")

    failed_response = client.post(
        "/api/aas/login",
        json={"account": "admin", "password": "wrong-password"},
    )
    login_response = client.post(
        "/api/aas/login",
        json={"account": "admin", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    logout_response = client.post(
        "/api/aas/logout",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert failed_response.status_code == 401
    assert login_response.status_code == 200
    assert logout_response.status_code == 200
    actions = list(
        db_session.scalars(
            select(AuditLog.action)
            .where(AuditLog.actor_id == admin.user_id)
            .order_by(AuditLog.log_id)
        )
    )
    assert actions == ["LOGIN_FAILED", "LOGIN_SUCCESS", "LOGOUT"]


def test_admin_can_filter_audit_logs(client, db_session):
    admin = create_user(db_session, account="admin", role="ADMIN")
    student = create_user(db_session, account="student02")
    db_session.add_all(
        [
            AuditLog(
                actor_id=admin.user_id,
                action="CREATE_USER",
                target_type="user",
                target_id=student.user_id,
                detail="新增帳號",
            ),
            AuditLog(
                actor_id=student.user_id,
                action="LOGIN_SUCCESS",
                target_type="user",
                target_id=student.user_id,
                detail="登入成功",
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/aas/audit-logs",
        headers=auth_headers(admin),
        params={
            "actor_id": admin.user_id,
            "action": "CREATE_USER",
            "target_type": "user",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["actor_name"] == admin.name
    assert payload[0]["action"] == "CREATE_USER"
    assert payload[0]["target_id"] == student.user_id


def test_non_admin_cannot_view_audit_logs(client, db_session):
    student = create_user(db_session)

    response = client.get(
        "/api/aas/audit-logs",
        headers=auth_headers(student),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "權限不足"


@pytest.mark.parametrize("limit", [0, 501])
def test_audit_log_limit_is_validated(client, db_session, limit):
    admin = create_user(db_session, account="admin", role="ADMIN")

    response = client.get(
        "/api/aas/audit-logs",
        headers=auth_headers(admin),
        params={"limit": limit},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "查詢筆數需介於 1 到 500"
