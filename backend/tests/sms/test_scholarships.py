import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.security import create_access_token, hash_password
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship, ScholarshipOption
from app.modules.sms.router import router


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
            AuditLog.__table__,
            Scholarship.__table__,
            ScholarshipOption.__table__,
            Application.__table__,
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


def make_unit(db_session):
    unit = Unit(name="高大獎助學金會", type="PRIVATE")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


def make_scholarship(db_session, unit, *, created_by=None):
    scholarship = Scholarship(
        unit_id=unit.unit_id,
        name="刪除測試獎學金",
        year=2026,
        amount=1000,
        quota=2,
        category="OTHER",
        status="OPEN",
        created_by=created_by,
    )
    db_session.add(scholarship)
    db_session.commit()
    db_session.refresh(scholarship)
    return scholarship


def test_list_returns_id_that_can_delete_scholarship(client, db_session):
    admin = make_user(db_session)
    unit = make_unit(db_session)
    scholarship = make_scholarship(db_session, unit, created_by=admin.user_id)

    listed = client.get("/api/sms/scholarships", headers=auth_headers(admin))
    assert listed.status_code == 200
    item = listed.json()[0]
    assert item["id"] == scholarship.scholarship_id
    assert "scholarshipId" not in item

    deleted = client.delete(f"/api/sms/scholarships/{item['id']}", headers=auth_headers(admin))
    assert deleted.status_code == 200
    assert deleted.json()["detail"] == "已刪除獎學金"
    assert db_session.get(Scholarship, scholarship.scholarship_id) is None

    actions = list(db_session.scalars(select(AuditLog.action).order_by(AuditLog.log_id)))
    assert actions == ["DELETE_SCHOLARSHIP"]
