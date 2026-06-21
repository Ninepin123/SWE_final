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
from app.modules.sas.models import (
    Application,
    ApplicationDocument,
    ApplicationEvent,
    StudentProfile,
    SupplementRequest,
)
from app.modules.sas.router import router
from app.modules.sms.models import Scholarship
from app.modules.trs.models import Recommendation


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
            ApplicationDocument.__table__,
            ApplicationEvent.__table__,
            SupplementRequest.__table__,
            StudentProfile.__table__,
            Notification.__table__,
            Recommendation.__table__,
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


def create_user(db_session, account, *, role="STUDENT", unit_id=None):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=account,
        role=role,
        unit_id=unit_id,
        department="資訊工程學系",
        gpa=3.8,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_student(db_session, account):
    return create_user(db_session, account)


def create_scholarship(db_session, *, deadline=None, require_recommendation=False):
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
        require_recommendation=require_recommendation,
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
    reviewer = create_user(
        db_session,
        "reviewer-for-submit",
        role="REVIEWER",
        unit_id=scholarship.unit_id,
    )

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

    document_response = client.post(
        f"/api/sas/applications/{draft['application_id']}/documents",
        headers=headers(student),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "這是一份用於申請的文字自傳內容。",
        },
    )
    assert document_response.status_code == 200

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
    reviewer_notification = db_session.scalar(
        select(Notification).where(Notification.user_id == reviewer.user_id)
    )
    assert reviewer_notification is not None
    assert reviewer_notification.title == "收到新的獎學金申請"


def test_required_recommendation_must_be_invited_before_submit(client, db_session):
    student = create_student(db_session, "student-recommendation-required")
    teacher = create_user(db_session, "teacher-recommendation-required", role="TEACHER")
    scholarship = create_scholarship(db_session, require_recommendation=True)
    create_response = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json=complete_payload(scholarship.scholarship_id),
    )
    application_id = create_response.json()["application_id"]
    client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "完整自傳內容",
        },
    )

    missing_response = client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    assert missing_response.status_code == 400
    assert "推薦信" in missing_response.json()["detail"]
    assert db_session.get(Application, application_id).status == "DRAFT"

    db_session.add(
        Recommendation(
            application_id=application_id,
            student_id=student.user_id,
            teacher_id=teacher.user_id,
            status="REQUESTED",
        )
    )
    db_session.commit()

    submit_response = client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "UNDER_REVIEW"


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
    client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "完整自傳內容",
        },
    )
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


def test_text_documents_can_be_created_updated_listed_and_deleted(client, db_session):
    student = create_student(db_session, "student06")
    scholarship = create_scholarship(db_session)
    draft = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json={"scholarship_id": scholarship.scholarship_id},
    ).json()
    application_id = draft["application_id"]

    create_response = client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "TRANSCRIPT",
            "title": "成績單內容",
            "content_text": "GPA 3.8，班級排名前百分之十。",
        },
    )
    assert create_response.status_code == 200
    document_id = create_response.json()["document_id"]

    update_response = client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "TRANSCRIPT",
            "title": "更新後成績單",
            "content_text": "GPA 3.8，班級排名前百分之五。",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["document_id"] == document_id
    assert update_response.json()["title"] == "更新後成績單"

    list_response = client.get(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    delete_response = client.delete(
        f"/api/sas/applications/{application_id}/documents/{document_id}",
        headers=headers(student),
    )
    assert delete_response.status_code == 200
    assert db_session.get(ApplicationDocument, document_id) is None


def test_submit_requires_at_least_one_text_document(client, db_session):
    student = create_student(db_session, "student07")
    scholarship = create_scholarship(db_session)
    draft = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json=complete_payload(scholarship.scholarship_id),
    ).json()

    response = client.post(
        f"/api/sas/applications/{draft['application_id']}/submit",
        headers=headers(student),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "請至少提交一份文字文件"


def test_documents_are_owner_only_and_locked_after_submit(client, db_session):
    owner = create_student(db_session, "student08")
    other = create_student(db_session, "student09")
    scholarship = create_scholarship(db_session)
    draft = client.post(
        "/api/sas/applications",
        headers=headers(owner),
        json=complete_payload(scholarship.scholarship_id),
    ).json()
    application_id = draft["application_id"]
    document = client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(owner),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "申請用自傳",
        },
    ).json()

    other_list = client.get(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(other),
    )
    assert other_list.status_code == 404

    client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(owner),
    )
    update_after_submit = client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(owner),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "修改自傳",
            "content_text": "嘗試在送出後修改",
        },
    )
    delete_after_submit = client.delete(
        f"/api/sas/applications/{application_id}/documents/{document['document_id']}",
        headers=headers(owner),
    )

    assert update_after_submit.status_code == 409
    assert delete_after_submit.status_code == 409


def create_submitted_application(client, db_session, student, scholarship):
    draft = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json=complete_payload(scholarship.scholarship_id),
    ).json()
    application_id = draft["application_id"]
    client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "完整自傳內容",
        },
    )
    client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )
    return application_id


def test_reviewer_can_request_and_student_can_submit_supplement(client, db_session):
    student = create_student(db_session, "supplement-student")
    scholarship = create_scholarship(db_session)
    reviewer = create_user(
        db_session,
        "reviewer01",
        role="REVIEWER",
        unit_id=scholarship.unit_id,
    )
    application_id = create_submitted_application(
        client, db_session, student, scholarship
    )
    deadline = datetime.now() + timedelta(days=3)

    request_response = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(reviewer),
        json={
            "required_items": "請補充家庭經濟狀況與成績說明",
            "deadline": deadline.isoformat(),
        },
    )
    assert request_response.status_code == 200
    request = request_response.json()
    assert request["status"] == "REQUESTED"
    assert request["can_submit"] is True
    assert db_session.get(Application, application_id).status == "NEED_SUPPLEMENT"

    list_response = client.get(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(student),
    )
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    submit_response = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests/{request['supplement_id']}/submit",
        headers=headers(student),
        json={"response_text": "補充家庭經濟狀況與本學期成績說明。"},
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["status"] == "SUBMITTED"
    assert submit_response.json()["can_submit"] is False
    assert db_session.get(Application, application_id).status == "UNDER_REVIEW"
    notifications = list(db_session.scalars(select(Notification)))
    assert any(item.user_id == student.user_id and item.title == "補件通知" for item in notifications)
    assert any(item.user_id == reviewer.user_id and item.title == "學生已完成補件" for item in notifications)


def test_reviewer_unit_isolation_and_duplicate_request(client, db_session):
    student = create_student(db_session, "supplement-student-2")
    scholarship = create_scholarship(db_session)
    other_unit = Unit(name="其他審查單位", type="SCHOOL")
    db_session.add(other_unit)
    db_session.commit()
    wrong_reviewer = create_user(
        db_session,
        "wrong-reviewer",
        role="REVIEWER",
        unit_id=other_unit.unit_id,
    )
    reviewer = create_user(
        db_session,
        "right-reviewer",
        role="REVIEWER",
        unit_id=scholarship.unit_id,
    )
    application_id = create_submitted_application(
        client, db_session, student, scholarship
    )
    payload = {
        "required_items": "補充文件",
        "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
    }

    forbidden = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(wrong_reviewer),
        json=payload,
    )
    first = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(reviewer),
        json=payload,
    )
    second = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(reviewer),
        json=payload,
    )

    assert forbidden.status_code == 403
    assert first.status_code == 200
    assert second.status_code == 409


def test_expired_or_other_students_supplement_cannot_be_submitted(client, db_session):
    owner = create_student(db_session, "supplement-owner")
    other = create_student(db_session, "supplement-other")
    scholarship = create_scholarship(db_session)
    reviewer = create_user(
        db_session,
        "reviewer02",
        role="REVIEWER",
        unit_id=scholarship.unit_id,
    )
    application_id = create_submitted_application(
        client, db_session, owner, scholarship
    )
    request_response = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests",
        headers=headers(reviewer),
        json={
            "required_items": "逾期測試",
            "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
        },
    )
    supplement_id = request_response.json()["supplement_id"]
    request = db_session.get(SupplementRequest, supplement_id)
    request.deadline = datetime.now() - timedelta(minutes=1)
    db_session.commit()

    other_response = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests/{supplement_id}/submit",
        headers=headers(other),
        json={"response_text": "越權補件"},
    )
    expired_response = client.post(
        f"/api/sas/applications/{application_id}/supplement-requests/{supplement_id}/submit",
        headers=headers(owner),
        json={"response_text": "逾期補件"},
    )

    assert other_response.status_code == 404
    assert expired_response.status_code == 409
    assert expired_response.json()["detail"] == "已超過補件期限"


def test_application_events_record_progress_and_are_owner_only(client, db_session):
    student = create_student(db_session, "event-owner")
    other = create_student(db_session, "event-other")
    scholarship = create_scholarship(db_session)
    draft = client.post(
        "/api/sas/applications",
        headers=headers(student),
        json=complete_payload(scholarship.scholarship_id),
    ).json()
    application_id = draft["application_id"]
    client.put(
        f"/api/sas/applications/{application_id}",
        headers=headers(student),
        json={"academic_note": "更新學業說明"},
    )
    client.post(
        f"/api/sas/applications/{application_id}/documents",
        headers=headers(student),
        json={
            "document_type": "AUTOBIOGRAPHY",
            "title": "自傳",
            "content_text": "事件測試自傳內容",
        },
    )
    client.post(
        f"/api/sas/applications/{application_id}/submit",
        headers=headers(student),
    )

    response = client.get(
        f"/api/sas/applications/{application_id}/events",
        headers=headers(student),
    )
    other_response = client.get(
        f"/api/sas/applications/{application_id}/events",
        headers=headers(other),
    )

    assert response.status_code == 200
    events = response.json()
    assert [event["event_type"] for event in events] == [
        "DRAFT_CREATED",
        "DRAFT_UPDATED",
        "DOCUMENT_CREATED",
        "APPLICATION_SUBMITTED",
    ]
    assert events[-1]["from_status"] == "DRAFT"
    assert events[-1]["to_status"] == "UNDER_REVIEW"
    assert events[0]["actor_name"] == student.name
    assert other_response.status_code == 404
