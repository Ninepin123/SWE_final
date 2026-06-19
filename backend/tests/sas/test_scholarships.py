from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import Unit, User
from app.modules.aas.security import create_access_token, hash_password
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


def create_user(db_session, account, *, department="資訊工程學系", gpa=3.75, role="STUDENT"):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=account,
        role=role,
        department=department,
        gpa=gpa,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_scholarship(db_session, unit, **overrides):
    values = {
        "unit_id": unit.unit_id,
        "name": "資訊學院獎學金",
        "year": 2026,
        "amount": 10000,
        "quota": 2,
        "min_gpa": 3.5,
        "department_limit": "資訊工程學系,資訊管理學系",
        "category": "MERIT",
        "description": "提供資訊學院學生申請",
        "deadline": datetime.now() + timedelta(days=30),
        "status": "OPEN",
    }
    values.update(overrides)
    scholarship = Scholarship(**values)
    db_session.add(scholarship)
    db_session.commit()
    db_session.refresh(scholarship)
    return scholarship


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


def test_eligible_student_can_apply(client, db_session):
    unit = Unit(name="資訊學院", type="SCHOOL", contact_email="cs@nuk.edu.tw")
    db_session.add(unit)
    db_session.commit()
    student = create_user(db_session, "student01")
    scholarship = create_scholarship(db_session, unit)

    response = client.get(
        "/api/sas/scholarships/available",
        headers=auth_headers(student),
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    item = payload[0]
    assert item["scholarship_id"] == scholarship.scholarship_id
    assert item["can_apply"] is True
    assert item["ineligibility_reasons"] == []
    assert item["remaining_quota"] == 2
    assert item["contact_email"] == "cs@nuk.edu.tw"


@pytest.mark.parametrize(
    ("student_kwargs", "scholarship_kwargs", "expected_reason"),
    [
        ({"gpa": 3.0}, {}, "GPA 未達門檻"),
        ({"department": "電機工程學系"}, {}, "科系不符合申請資格"),
        ({}, {"deadline": datetime.now() - timedelta(days=1)}, "已超過申請截止時間"),
        ({}, {"status": "CLOSED"}, "獎學金目前未開放申請"),
    ],
)
def test_ineligible_reasons_are_returned(
    client,
    db_session,
    student_kwargs,
    scholarship_kwargs,
    expected_reason,
):
    unit = Unit(name="測試單位", type="SCHOOL")
    db_session.add(unit)
    db_session.commit()
    student = create_user(db_session, "student02", **student_kwargs)
    create_scholarship(db_session, unit, **scholarship_kwargs)

    response = client.get(
        "/api/sas/scholarships/available",
        headers=auth_headers(student),
    )

    assert response.status_code == 200
    item = response.json()[0]
    assert item["can_apply"] is False
    assert any(expected_reason in reason for reason in item["ineligibility_reasons"])


def test_existing_application_and_quota_are_reflected(client, db_session):
    unit = Unit(name="學務處", type="SCHOOL")
    db_session.add(unit)
    db_session.commit()
    student = create_user(db_session, "student03")
    other_student = create_user(db_session, "student04")
    scholarship = create_scholarship(db_session, unit, quota=2)
    db_session.add_all(
        [
            Application(
                student_id=student.user_id,
                scholarship_id=scholarship.scholarship_id,
                status="UNDER_REVIEW",
            ),
            Application(
                student_id=other_student.user_id,
                scholarship_id=scholarship.scholarship_id,
                status="UNDER_REVIEW",
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/sas/scholarships/available",
        headers=auth_headers(student),
    )

    item = response.json()[0]
    assert item["remaining_quota"] == 0
    assert item["already_applied"] is True
    assert "申請名額已滿" in item["ineligibility_reasons"]
    assert "已申請過此獎學金" in item["ineligibility_reasons"]


def test_filters_and_eligible_only(client, db_session):
    unit = Unit(name="教育部", type="GOVERNMENT")
    db_session.add(unit)
    db_session.commit()
    student = create_user(db_session, "student05")
    create_scholarship(db_session, unit, name="符合資格獎學金", category="GOVERNMENT")
    create_scholarship(
        db_session,
        unit,
        name="不符合資格獎學金",
        category="PRIVATE",
        min_gpa=4.0,
    )

    response = client.get(
        "/api/sas/scholarships/available",
        headers=auth_headers(student),
        params={"keyword": "符合資格", "category": "GOVERNMENT", "eligible_only": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["name"] for item in payload] == ["符合資格獎學金"]


def test_non_student_cannot_query_available_scholarships(client, db_session):
    teacher = create_user(db_session, "teacher01", role="TEACHER")

    response = client.get(
        "/api/sas/scholarships/available",
        headers=auth_headers(teacher),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "權限不足"
