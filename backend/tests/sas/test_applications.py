from datetime import datetime, timedelta

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
from app.modules.sas.models import Application, StudentProfile
from app.modules.sas.router import router
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
        tables=[
            Unit.__table__,
            User.__table__,
            Scholarship.__table__,
            Application.__table__,
            StudentProfile.__table__,
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


def create_student(db_session, account):
    student = User(
        account=account,
        password=hash_password("password123"),
        name=account,
        role="STUDENT",
        department="資訊工程學系",
        gpa=3.8,
        status="ACTIVE",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)
    return student


def create_scholarship(db_session, *, deadline=None):
    unit = db_session.scalar(select(Unit).where(Unit.name == "學務處"))
    if unit is None:
        unit = Unit(name="學務處", type="SCHOOL")
        db_session.add(unit)
        db_session.flush()
    scholarship = Scholarship(
        unit_id=unit.unit_id,
        name=f"測試獎學金-{datetime.now().timestamp()}",
        year=2026,
        amount=10000,
        quota=3,
        min_gpa=3.0,
        department_limit="資訊工程學系",
        category="MERIT",
        deadline=deadline or datetime.now() + timedelta(days=30),
        status="OPEN",
    )
    db_session.add(scholarship)
    db_session.commit()
    db_session.refresh(scholarship)
    return scholarship


def headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


def complete_payload(scholarship_id):
    return {
        "scholarship_id": scholarship_id,
        "statement": "我希望透過本獎學金支持學習與專題研究，持續精進專業能力。",
        "contact_phone": "0912345678",
        "address": "高雄市楠梓區",
        "household_status": "家庭經濟狀況需要獎學金協助",
        "academic_note": "學業表現穩定",
    }


def test_student_can_create_update_and_submit_draft(client, db_session):
    student = create_student(db_session, "student01")
    scholarship = create_scholarship(db_session)

    create_response = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json={"scholarship_id": scholarship.scholarship_id, "statement": "尚未完成"},
    )
    assert create_response.status_code == 201
    draft = create_response.json()
    assert draft["status"] == "DRAFT"
    assert draft["submitted_at"] is None
    assert draft["can_edit"] is True

    update_response = client.put(
        f"/api/sas/applications/{draft['application_id']}",
        headers=headers(student),
        json={key: value for key, value in complete_payload(scholarship.scholarship_id).items() if key != "scholarship_id"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["contact_phone"] == "0912345678"

    submit_response = client.post(
        f"/api/sas/applications/{draft['application_id']}/submit",
        headers=headers(student),
    )
    assert submit_response.status_code == 200
    submitted = submit_response.json()
    assert submitted["status"] == "UNDER_REVIEW"
    assert submitted["submitted_at"] is not None
    assert submitted["can_edit"] is False
    notification = db_session.scalar(
        select(Notification).where(Notification.user_id == student.user_id)
    )
    assert notification is not None


def test_incomplete_draft_cannot_be_submitted(client, db_session):
    student = create_student(db_session, "student02")
    scholarship = create_scholarship(db_session)
    response = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json={"scholarship_id": scholarship.scholarship_id, "statement": "未完成"},
    )
    application_id = response.json()["application_id"]

    submit_response = client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    assert submit_response.status_code == 400
    assert "申請資料不完整" in submit_response.json()["detail"]
    app = db_session.get(Application, application_id)
    assert app.status == "DRAFT"


def test_submitted_application_cannot_be_edited_or_submitted_again(client, db_session):
    student = create_student(db_session, "student03")
    scholarship = create_scholarship(db_session)
    create_response = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json=complete_payload(scholarship.scholarship_id),
    )
    application_id = create_response.json()["application_id"]
    client.post(f"/api/sas/applications/{application_id}/submit", headers=headers(student))

    update_response = client.put(
        f"/api/sas/applications/{application_id}",
        headers=headers(student),
        json={"statement": "嘗試修改"},
    )
    submit_response = client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    assert update_response.status_code == 409
    assert submit_response.status_code == 409


def test_student_cannot_access_another_students_application(client, db_session):
    owner = create_student(db_session, "owner")
    other = create_student(db_session, "other")
    scholarship = create_scholarship(db_session)
    create_response = client.post(
        "/api/sas/applications",
        headers=headers(owner),
        json={"scholarship_id": scholarship.scholarship_id},
    )
    application_id = create_response.json()["application_id"]

    get_response = client.get(
        f"/api/sas/applications/{application_id}",
        headers=headers(other),
    )
    update_response = client.put(
        f"/api/sas/applications/{application_id}",
        headers=headers(other),
        json={"statement": "越權修改"},
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404


def test_expired_draft_is_locked(client, db_session):
    student = create_student(db_session, "student04")
    scholarship = create_scholarship(db_session)
    create_response = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json={"scholarship_id": scholarship.scholarship_id},
    )
    application_id = create_response.json()["application_id"]
    scholarship.deadline = datetime.now() - timedelta(minutes=1)
    db_session.commit()

    update_response = client.put(
        f"/api/sas/applications/{application_id}",
        headers=headers(student),
        json={"statement": "逾期修改"},
    )
    submit_response = client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    assert update_response.status_code == 409
    assert "草稿已鎖定" in update_response.json()["detail"]
    assert submit_response.status_code == 409


def test_duplicate_draft_is_rejected(client, db_session):
    student = create_student(db_session, "student05")
    scholarship = create_scholarship(db_session)
    payload = {"scholarship_id": scholarship.scholarship_id}

    first = client.post("/api/sas/applications", headers=headers(student), json=payload)
    second = client.post("/api/sas/applications", headers=headers(student), json=payload)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["detail"] == "此獎學金已有申請或草稿"
