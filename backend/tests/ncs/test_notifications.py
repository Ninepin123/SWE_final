import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import Unit, User
from app.modules.aas.security import create_access_token, hash_password
from app.modules.ncs.models import Notification
from app.modules.ncs.router import router
from app.modules.ncs import service as ncs_service


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(
        engine,
        tables=[
            Unit.__table__,
            User.__table__,
            Notification.__table__,
        ],
    )
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


def create_user(db_session, account, *, role="STUDENT"):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=account,
        role=role,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_notification(db_session, *, user_id, title, body="body", is_read=False):
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        is_read=is_read,
    )
    db_session.add(notification)
    db_session.commit()
    db_session.refresh(notification)
    return notification


def auth(user):
    token = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def test_tc1_create_notification_success(db_session):
    user = create_user(db_session, "student01")

    created = ncs_service.create_notification(
        db_session,
        user_id=user.user_id,
        title="測試通知",
        body="這是一則測試通知",
    )

    assert created.notification_id is not None
    assert created.is_read is False
    stored = db_session.get(Notification, created.notification_id)
    assert stored is not None
    assert stored.title == "測試通知"


def test_tc2_user_can_only_see_own_notifications(client, db_session):
    user_a = create_user(db_session, "student-a")
    user_b = create_user(db_session, "student-b")
    create_notification(db_session, user_id=user_a.user_id, title="A 通知")
    create_notification(db_session, user_id=user_b.user_id, title="B 通知")

    response = client.get("/api/ncs/notifications", headers=auth(user_a))

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["user_id"] == user_a.user_id
    assert payload[0]["title"] == "A 通知"


def test_tc3_unread_count_is_correct(client, db_session):
    user_a = create_user(db_session, "student-count")
    create_notification(db_session, user_id=user_a.user_id, title="未讀-1", is_read=False)
    create_notification(db_session, user_id=user_a.user_id, title="未讀-2", is_read=False)
    create_notification(db_session, user_id=user_a.user_id, title="已讀", is_read=True)

    response = client.get("/api/ncs/notifications/unread-count", headers=auth(user_a))

    assert response.status_code == 200
    assert response.json() == {"unread_count": 2}


def test_tc4_mark_single_notification_read_success(client, db_session):
    user_a = create_user(db_session, "student-read")
    notification = create_notification(db_session, user_id=user_a.user_id, title="待讀")

    response = client.patch(
        f"/api/ncs/notifications/{notification.notification_id}/read",
        headers=auth(user_a),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["notification_id"] == notification.notification_id
    assert payload["is_read"] is True
    db_session.expire_all()
    assert db_session.get(Notification, notification.notification_id).is_read is True


def test_tc5_cannot_mark_other_users_notification(client, db_session):
    user_a = create_user(db_session, "student-owner-a")
    user_b = create_user(db_session, "student-owner-b")
    notification_b = create_notification(db_session, user_id=user_b.user_id, title="B 未讀")

    response = client.patch(
        f"/api/ncs/notifications/{notification_b.notification_id}/read",
        headers=auth(user_a),
    )

    assert response.status_code == 403
    db_session.expire_all()
    assert db_session.get(Notification, notification_b.notification_id).is_read is False


def test_tc6_mark_all_read_only_affects_current_user(client, db_session):
    user_a = create_user(db_session, "student-markall-a")
    user_b = create_user(db_session, "student-markall-b")
    a1 = create_notification(db_session, user_id=user_a.user_id, title="A-1")
    a2 = create_notification(db_session, user_id=user_a.user_id, title="A-2")
    b1 = create_notification(db_session, user_id=user_b.user_id, title="B-1")

    response = client.patch("/api/ncs/notifications/read-all", headers=auth(user_a))

    assert response.status_code == 200
    assert response.json() == {"updated_count": 2}
    db_session.expire_all()
    assert db_session.get(Notification, a1.notification_id).is_read is True
    assert db_session.get(Notification, a2.notification_id).is_read is True
    assert db_session.get(Notification, b1.notification_id).is_read is False


def test_tc7_unread_only_filter(client, db_session):
    user_a = create_user(db_session, "student-filter")
    create_notification(db_session, user_id=user_a.user_id, title="已讀", is_read=True)
    create_notification(db_session, user_id=user_a.user_id, title="未讀", is_read=False)

    response = client.get(
        "/api/ncs/notifications",
        params={"unread_only": True},
        headers=auth(user_a),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["is_read"] is False
    assert payload[0]["title"] == "未讀"


def test_tc8_unauthenticated_cannot_list_notifications(client):
    response = client.get("/api/ncs/notifications")

    assert response.status_code in {401, 403}


def test_tc9_non_admin_cannot_create_notification_but_admin_can(client, db_session):
    student = create_user(db_session, "student-create", role="STUDENT")
    admin = create_user(db_session, "admin-create", role="ADMIN")
    target_user = create_user(db_session, "target-user", role="STUDENT")
    payload = {
        "user_id": target_user.user_id,
        "title": "管理員通知",
        "body": "Admin 建立測試",
        "category": "SYSTEM",
    }

    denied = client.post("/api/ncs/notifications", json=payload, headers=auth(student))
    allowed = client.post("/api/ncs/notifications", json=payload, headers=auth(admin))

    assert denied.status_code == 403
    assert allowed.status_code == 201
    created = allowed.json()
    assert created["user_id"] == target_user.user_id
    assert created["is_read"] is False
    stored = db_session.scalar(
        select(Notification).where(Notification.notification_id == created["notification_id"])
    )
    assert stored is not None
