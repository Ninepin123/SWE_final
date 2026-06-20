import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.router import router
from app.modules.aas.security import create_access_token, hash_password
from app.modules.sms.models import Scholarship


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
        tables=[Unit.__table__, User.__table__, AuditLog.__table__, Scholarship.__table__],
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


def make_user(db_session, *, account="admin", role="ADMIN", unit_id=None):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=f"{role} user",
        role=role,
        status="ACTIVE",
        unit_id=unit_id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


def test_admin_can_create_list_update_and_delete_unit(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")

    created = client.post(
        "/api/aas/units",
        headers=auth_headers(admin),
        json={"name": "學生事務處", "type": "SCHOOL", "contact_email": "osa@nuk.edu.tw"},
    )
    assert created.status_code == 201
    unit_id = created.json()["unit_id"]
    assert created.json()["type"] == "SCHOOL"

    listed = client.get("/api/aas/units", headers=auth_headers(admin))
    assert listed.status_code == 200
    assert [u["unit_id"] for u in listed.json()] == [unit_id]

    updated = client.put(
        f"/api/aas/units/{unit_id}",
        headers=auth_headers(admin),
        json={"name": "學生事務處（總務）", "type": "OTHER"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "學生事務處（總務）"
    assert updated.json()["type"] == "OTHER"

    deleted = client.delete(f"/api/aas/units/{unit_id}", headers=auth_headers(admin))
    assert deleted.status_code == 200
    assert db_session.get(Unit, unit_id) is None

    actions = list(db_session.scalars(select(AuditLog.action).order_by(AuditLog.log_id)))
    assert actions == ["CREATE_UNIT", "UPDATE_UNIT", "DELETE_UNIT"]


def test_duplicate_unit_name_is_rejected(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")
    db_session.add(Unit(name="教務處", type="SCHOOL"))
    db_session.commit()

    response = client.post(
        "/api/aas/units",
        headers=auth_headers(admin),
        json={"name": "教務處", "type": "SCHOOL"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "單位名稱已存在"


def test_invalid_unit_type_is_rejected(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")

    response = client.post(
        "/api/aas/units",
        headers=auth_headers(admin),
        json={"name": "未知類型單位", "type": "UNKNOWN"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "單位類型不存在"


def test_non_admin_can_read_but_not_write_units(client, db_session):
    student = make_user(db_session, account="student", role="STUDENT")
    db_session.add(Unit(name="圖書館", type="SCHOOL"))
    db_session.commit()

    read = client.get("/api/aas/units", headers=auth_headers(student))
    assert read.status_code == 200
    assert len(read.json()) == 1

    write = client.post(
        "/api/aas/units",
        headers=auth_headers(student),
        json={"name": "想偷建的單位", "type": "OTHER"},
    )
    assert write.status_code == 403
    assert write.json()["detail"] == "權限不足"


def test_cannot_delete_unit_with_bound_user(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")
    unit = Unit(name="資工系", type="SCHOOL")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    make_user(db_session, account="sponsor", role="SPONSOR", unit_id=unit.unit_id)

    response = client.delete(f"/api/aas/units/{unit.unit_id}", headers=auth_headers(admin))
    assert response.status_code == 409
    assert "帳號" in response.json()["detail"]
    assert db_session.get(Unit, unit.unit_id) is not None


def test_cannot_delete_unit_with_bound_scholarship(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")
    unit = Unit(name="校友會", type="PRIVATE")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    db_session.add(Scholarship(unit_id=unit.unit_id, name="校友獎學金", year=2026, amount=10000, quota=1))
    db_session.commit()

    response = client.delete(f"/api/aas/units/{unit.unit_id}", headers=auth_headers(admin))
    assert response.status_code == 409
    assert "獎學金" in response.json()["detail"]
