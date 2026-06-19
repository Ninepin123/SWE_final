import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import Unit, User
from app.modules.aas.security import create_access_token, hash_password
from app.modules.sas.models import StudentProfile
from app.modules.sas.router import router


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
        tables=[Unit.__table__, User.__table__, StudentProfile.__table__],
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


def create_user(db_session, *, account, role="STUDENT"):
    user = User(
        account=account,
        password=hash_password("password123"),
        name="測試學生" if role == "STUDENT" else "測試使用者",
        email=f"{account}@nuk.edu.tw",
        role=role,
        department="資訊工程學系",
        gpa=3.75,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


def test_student_can_view_own_profile(client, db_session):
    student = create_user(db_session, account="A1125001")
    db_session.add(
        StudentProfile(
            user_id=student.user_id,
            grade="三年級",
            identity_type="一般生",
            contact_phone="0912345678",
            address="高雄市楠梓區",
        )
    )
    db_session.commit()

    response = client.get("/api/sas/profile", headers=auth_headers(student))

    assert response.status_code == 200
    payload = response.json()
    assert payload["account"] == "A1125001"
    assert payload["name"] == "測試學生"
    assert payload["department"] == "資訊工程學系"
    assert payload["grade"] == "三年級"
    assert payload["gpa"] == 3.75
    assert payload["identity_type"] == "一般生"
    assert payload["contact_phone"] == "0912345678"


def test_student_can_create_and_update_editable_profile_fields(client, db_session):
    student = create_user(db_session, account="A1125002")

    response = client.put(
        "/api/sas/profile",
        headers=auth_headers(student),
        json={
            "email": "new-email@nuk.edu.tw",
            "contact_phone": "0987654321",
            "address": "高雄市左營區",
            "emergency_contact_name": "王先生",
            "emergency_contact_phone": "0911000000",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "new-email@nuk.edu.tw"
    assert payload["contact_phone"] == "0987654321"
    profile = db_session.get(StudentProfile, student.user_id)
    assert profile.contact_email == "new-email@nuk.edu.tw"
    assert profile.emergency_contact_name == "王先生"
    db_session.refresh(student)
    assert student.email == "A1125002@nuk.edu.tw"


def test_core_identity_fields_cannot_be_updated(client, db_session):
    student = create_user(db_session, account="A1125003")

    response = client.put(
        "/api/sas/profile",
        headers=auth_headers(student),
        json={
            "account": "CHANGED",
            "name": "修改姓名",
            "department": "其他科系",
            "grade": "四年級",
            "gpa": 4.3,
            "identity_type": "特殊身份",
            "contact_phone": "0900000000",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["account"] == "A1125003"
    assert payload["name"] == "測試學生"
    assert payload["department"] == "資訊工程學系"
    assert payload["gpa"] == 3.75
    assert payload["grade"] is None
    assert payload["identity_type"] is None


def test_non_student_cannot_access_profile(client, db_session):
    teacher = create_user(db_session, account="teacher", role="TEACHER")

    response = client.get("/api/sas/profile", headers=auth_headers(teacher))

    assert response.status_code == 403
    assert response.json()["detail"] == "權限不足"


def test_invalid_email_is_rejected(client, db_session):
    student = create_user(db_session, account="A1125004")

    response = client.put(
        "/api/sas/profile",
        headers=auth_headers(student),
        json={"email": "invalid-email"},
    )

    assert response.status_code == 422
    assert db_session.get(StudentProfile, student.user_id) is None
