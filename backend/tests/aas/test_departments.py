import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Department, Unit, User
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
    Base.metadata.create_all(
        engine,
        tables=[Unit.__table__, User.__table__, Department.__table__, AuditLog.__table__],
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


def make_user(db_session, *, account="admin", role="ADMIN", department=None):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=f"{role} user",
        role=role,
        status="ACTIVE",
        department=department,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


def test_admin_can_create_list_update_and_delete_department(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")

    created = client.post(
        "/api/aas/departments",
        headers=auth_headers(admin),
        json={"name": "資訊工程學系", "college": "資訊學院", "category": "ACADEMIC"},
    )
    assert created.status_code == 201
    department_id = created.json()["department_id"]
    assert created.json()["category"] == "ACADEMIC"
    assert created.json()["college"] == "資訊學院"

    listed = client.get("/api/aas/departments", headers=auth_headers(admin))
    assert listed.status_code == 200
    assert [d["department_id"] for d in listed.json()] == [department_id]

    updated = client.put(
        f"/api/aas/departments/{department_id}",
        headers=auth_headers(admin),
        json={"name": "資訊管理學系", "category": "ADMIN"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "資訊管理學系"
    assert updated.json()["category"] == "ADMIN"

    deleted = client.delete(f"/api/aas/departments/{department_id}", headers=auth_headers(admin))
    assert deleted.status_code == 200
    assert db_session.get(Department, department_id) is None

    actions = list(db_session.scalars(select(AuditLog.action).order_by(AuditLog.log_id)))
    assert actions == ["CREATE_DEPARTMENT", "UPDATE_DEPARTMENT", "DELETE_DEPARTMENT"]


def test_duplicate_department_name_is_rejected(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")
    db_session.add(Department(name="電機工程學系", category="ACADEMIC"))
    db_session.commit()

    response = client.post(
        "/api/aas/departments",
        headers=auth_headers(admin),
        json={"name": "電機工程學系"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "科系／部門名稱已存在"


def test_invalid_department_category_is_rejected(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")

    response = client.post(
        "/api/aas/departments",
        headers=auth_headers(admin),
        json={"name": "未知類別科系", "category": "UNKNOWN"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "科系類別不存在"


def test_non_admin_can_read_but_not_write_departments(client, db_session):
    student = make_user(db_session, account="student", role="STUDENT")
    db_session.add(Department(name="土木與環境工程學系", category="ACADEMIC"))
    db_session.commit()

    read = client.get("/api/aas/departments", headers=auth_headers(student))
    assert read.status_code == 200
    assert len(read.json()) == 1

    write = client.post(
        "/api/aas/departments",
        headers=auth_headers(student),
        json={"name": "想偷建的科系"},
    )
    assert write.status_code == 403
    assert write.json()["detail"] == "權限不足"


def test_cannot_delete_department_with_bound_user(client, db_session):
    admin = make_user(db_session, account="admin", role="ADMIN")
    department = Department(name="應用數學系", category="ACADEMIC")
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    make_user(db_session, account="student", role="STUDENT", department="應用數學系")

    response = client.delete(
        f"/api/aas/departments/{department.department_id}", headers=auth_headers(admin)
    )
    assert response.status_code == 409
    assert "帳號" in response.json()["detail"]
    assert db_session.get(Department, department.department_id) is not None
