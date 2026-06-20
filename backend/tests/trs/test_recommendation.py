from datetime import datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.security import create_access_token, hash_password
from app.modules.ncs.models import Notification
from app.modules.ras.models import Review
from app.modules.sas.models import Application, ApplicationDocument, StudentProfile
from app.modules.sms.models import Scholarship
from app.modules.trs.models import Recommendation
from app.modules.trs.router import router


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
            Application.__table__,
            StudentProfile.__table__,
            ApplicationDocument.__table__,
            Recommendation.__table__,
            Review.__table__,
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


def auth_headers(user):
    token = create_access_token(user.user_id, user.role)
    return {"Authorization": f"Bearer {token}"}


def mk_unit(db_session, name="學務處"):
    unit = Unit(name=name, type="SCHOOL")
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


def mk_user(db_session, account, *, role="STUDENT", unit_id=None, name=None):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=name or account,
        role=role,
        unit_id=unit_id,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def mk_scholarship(db_session, unit_id, *, name=None, deadline=None):
    scholarship = Scholarship(
        unit_id=unit_id,
        name=name or f"獎學金-{datetime.now().timestamp()}",
        year=2026,
        amount=10000,
        quota=10,
        category="MERIT",
        deadline=deadline or (datetime.now() + timedelta(days=30)),
        status="OPEN",
    )
    db_session.add(scholarship)
    db_session.commit()
    db_session.refresh(scholarship)
    return scholarship


def mk_application(db_session, student_id, scholarship_id):
    app = Application(student_id=student_id, scholarship_id=scholarship_id, status="UNDER_REVIEW")
    db_session.add(app)
    db_session.commit()
    db_session.refresh(app)
    return app


def mk_recommendation(db_session, *, application_id, student_id, teacher_id, status="REQUESTED", content=None):
    rec = Recommendation(
        application_id=application_id,
        student_id=student_id,
        teacher_id=teacher_id,
        status=status,
        content=content,
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)
    return rec


def mk_profile(db_session, user_id):
    profile = StudentProfile(
        user_id=user_id,
        grade="三年級",
        identity_type="一般生",
        contact_email="student01@nuk.edu.tw",
        contact_phone="0912345678",
        address="高雄市楠梓區大學路 1 號",
        emergency_contact_name="家長",
        emergency_contact_phone="0987654321",
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def mk_document(db_session, application_id, *, document_type="AUTOBIOGRAPHY", title="自傳", content_text="文件內容"):
    document = ApplicationDocument(
        application_id=application_id,
        document_type=document_type,
        title=title,
        content_text=content_text,
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)
    return document


@pytest.fixture()
def scenario(db_session):
    unit = mk_unit(db_session)
    student = mk_user(db_session, "student01", role="STUDENT")
    teacher_a = mk_user(db_session, "teacherA", role="TEACHER")
    teacher_b = mk_user(db_session, "teacherB", role="TEACHER")
    scholarship = mk_scholarship(db_session, unit_id=unit.unit_id)
    application = mk_application(db_session, student.user_id, scholarship.scholarship_id)

    rec_a = mk_recommendation(
        db_session,
        application_id=application.application_id,
        student_id=student.user_id,
        teacher_id=teacher_a.user_id,
    )
    rec_b = mk_recommendation(
        db_session,
        application_id=application.application_id,
        student_id=student.user_id,
        teacher_id=teacher_b.user_id,
    )

    return {
        "unit": unit,
        "student": student,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "scholarship": scholarship,
        "application": application,
        "rec_a": rec_a,
        "rec_b": rec_b,
    }


def test_teacher_can_only_list_own_recommendations(client, scenario):
    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["rec_id"] == scenario["rec_a"].rec_id
    assert rows[0]["teacher_id"] == scenario["teacher_a"].user_id


def test_teacher_can_save_draft(client, db_session, scenario):
    response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "這是一封草稿推薦信", "submit": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "DRAFT"
    assert payload["content"] == "這是一封草稿推薦信"

    db_session.refresh(scenario["rec_a"])
    assert scenario["rec_a"].status == "DRAFT"
    assert scenario["rec_a"].content == "這是一封草稿推薦信"


def test_teacher_can_submit_recommendation(client, db_session, scenario):
    response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "正式推薦內容", "submit": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "SUBMITTED"
    assert payload["content"] == "正式推薦內容"
    assert payload["submitted_at"] is not None

    db_session.refresh(scenario["rec_a"])
    assert scenario["rec_a"].status == "SUBMITTED"
    assert scenario["rec_a"].content == "正式推薦內容"


def test_submitted_recommendation_cannot_be_modified(client, db_session, scenario):
    submit_response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "第一版正式內容", "submit": True},
    )
    assert submit_response.status_code == 200

    locked_response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "嘗試覆寫內容", "submit": False},
    )

    assert locked_response.status_code == 409

    db_session.refresh(scenario["rec_a"])
    assert scenario["rec_a"].content == "第一版正式內容"
    assert scenario["rec_a"].status == "SUBMITTED"


def test_other_teacher_cannot_modify_recommendation(client, scenario):
    response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_b"]),
        json={"content": "越權修改", "submit": False},
    )

    assert response.status_code == 403


def test_student_status_endpoint_does_not_expose_content(client, scenario):
    client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "正式推薦內容", "submit": True},
    )

    response = client.get(
        "/api/trs/recommendations/student",
        headers=auth_headers(scenario["student"]),
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    assert all("content" not in item for item in rows)
    assert all("draft_content" not in item for item in rows)
    assert all("letter_content" not in item for item in rows)
    assert {item["status"] for item in rows} >= {"REQUESTED", "SUBMITTED"}


def test_student_status_response_only_contains_privacy_safe_fields(client, scenario):
    response = client.get(
        "/api/trs/recommendations/student",
        headers=auth_headers(scenario["student"]),
    )

    assert response.status_code == 200
    rows = response.json()
    allowed = {
        "rec_id",
        "application_id",
        "teacher_id",
        "teacher_name",
        "status",
        "submitted_at",
        "deadline",
        "scholarship_name",
        "updated_at",
    }
    for item in rows:
        assert set(item.keys()).issubset(allowed)
        assert "content" not in item
        assert "token" not in item
        assert "session_token" not in item


def test_owner_teacher_can_view_student_profile(client, db_session, scenario):
    mk_profile(db_session, scenario["student"].user_id)
    document = mk_document(db_session, scenario["application"].application_id, title="自傳", content_text="我是學生")

    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["student"]["user_id"] == scenario["student"].user_id
    assert payload["application"]["application_id"] == scenario["application"].application_id
    assert payload["scholarship"]["scholarship_id"] == scenario["application"].scholarship_id
    assert payload["documents"][0]["document_id"] == document.document_id
    assert "content" not in payload
    assert "session_token" not in payload["student"]
    assert "password" not in payload["student"]


def test_other_teacher_cannot_view_student_profile(client, scenario):
    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["teacher_b"]),
    )

    assert response.status_code == 403


def test_student_cannot_view_teacher_student_profile_endpoint(client, scenario):
    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["student"]),
    )

    assert response.status_code == 403


def test_missing_recommendation_profile_returns_404(client, scenario):
    response = client.get(
        "/api/trs/recommendations/999999/student-profile",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 404


def test_student_profile_endpoint_returns_empty_documents_when_missing(client, db_session, scenario):
    mk_profile(db_session, scenario["student"].user_id)

    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    assert response.json()["documents"] == []


def test_student_profile_endpoint_returns_null_profile_when_missing(client, scenario):
    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    assert response.json()["profile"] is None


def test_teacher_list_supports_keyword_search(client, db_session, scenario):
    student = mk_user(db_session, "A1125002", role="STUDENT", name="王小明")
    scholarship = mk_scholarship(db_session, scenario["unit"].unit_id, name="特殊獎助學金")
    application = mk_application(db_session, student.user_id, scholarship.scholarship_id)
    rec = mk_recommendation(
        db_session,
        application_id=application.application_id,
        student_id=student.user_id,
        teacher_id=scenario["teacher_a"].user_id,
    )

    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"keyword": "特殊"},
    )

    assert response.status_code == 200
    rows = response.json()
    assert [row["rec_id"] for row in rows] == [rec.rec_id]


def test_teacher_list_supports_status_filter(client, db_session, scenario):
    scenario["rec_a"].status = "DRAFT"
    db_session.commit()

    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"status": "DRAFT"},
    )

    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert all(row["status"] == "DRAFT" for row in rows)


def test_teacher_list_sorts_by_deadline_asc(client, db_session, scenario):
    student_2 = mk_user(db_session, "A1125003", role="STUDENT", name="學生二")
    early_scholarship = mk_scholarship(
        db_session,
        scenario["unit"].unit_id,
        name="早截止獎學金",
        deadline=datetime.now() + timedelta(days=1),
    )
    late_scholarship = mk_scholarship(
        db_session,
        scenario["unit"].unit_id,
        name="晚截止獎學金",
        deadline=datetime.now() + timedelta(days=10),
    )
    early_app = mk_application(db_session, student_2.user_id, early_scholarship.scholarship_id)
    late_app = mk_application(db_session, scenario["student"].user_id, late_scholarship.scholarship_id)
    early_rec = mk_recommendation(
        db_session,
        application_id=early_app.application_id,
        student_id=student_2.user_id,
        teacher_id=scenario["teacher_a"].user_id,
    )
    late_rec = mk_recommendation(
        db_session,
        application_id=late_app.application_id,
        student_id=scenario["student"].user_id,
        teacher_id=scenario["teacher_a"].user_id,
    )

    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"sort_by": "deadline", "order": "asc"},
    )

    assert response.status_code == 200
    rec_ids = [row["rec_id"] for row in response.json()]
    assert rec_ids.index(early_rec.rec_id) < rec_ids.index(late_rec.rec_id)


def test_teacher_list_sorts_by_deadline_desc(client, db_session, scenario):
    student_2 = mk_user(db_session, "A1125004", role="STUDENT", name="學生三")
    early_scholarship = mk_scholarship(
        db_session,
        scenario["unit"].unit_id,
        name="早截止獎學金B",
        deadline=datetime.now() + timedelta(days=2),
    )
    late_scholarship = mk_scholarship(
        db_session,
        scenario["unit"].unit_id,
        name="晚截止獎學金B",
        deadline=datetime.now() + timedelta(days=9),
    )
    early_app = mk_application(db_session, student_2.user_id, early_scholarship.scholarship_id)
    late_app = mk_application(db_session, scenario["student"].user_id, late_scholarship.scholarship_id)
    early_rec = mk_recommendation(
        db_session,
        application_id=early_app.application_id,
        student_id=student_2.user_id,
        teacher_id=scenario["teacher_a"].user_id,
    )
    late_rec = mk_recommendation(
        db_session,
        application_id=late_app.application_id,
        student_id=scenario["student"].user_id,
        teacher_id=scenario["teacher_a"].user_id,
    )

    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"sort_by": "deadline", "order": "desc"},
    )

    assert response.status_code == 200
    rec_ids = [row["rec_id"] for row in response.json()]
    assert rec_ids.index(late_rec.rec_id) < rec_ids.index(early_rec.rec_id)


def test_search_filter_does_not_cross_teacher_scope(client, db_session, scenario):
    other_student = mk_user(db_session, "A1125005", role="STUDENT", name="跨教師關鍵字")
    scholarship = mk_scholarship(db_session, scenario["unit"].unit_id, name="一般獎學金")
    application = mk_application(db_session, other_student.user_id, scholarship.scholarship_id)
    mk_recommendation(
        db_session,
        application_id=application.application_id,
        student_id=other_student.user_id,
        teacher_id=scenario["teacher_b"].user_id,
    )

    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"keyword": "跨教師關鍵字"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_teacher_dashboard_counts_only_own_recommendations(client, db_session, scenario):
    unit = mk_unit(db_session, name="第二單位")
    pending_student = mk_user(db_session, "A1125010", role="STUDENT", name="待處理學生")
    draft_student = mk_user(db_session, "A1125011", role="STUDENT", name="草稿學生")
    submitted_student = mk_user(db_session, "A1125012", role="STUDENT", name="已提交學生")
    due_soon_student = mk_user(db_session, "A1125013", role="STUDENT", name="即將截止學生")
    overdue_student = mk_user(db_session, "A1125014", role="STUDENT", name="逾期學生")
    other_teacher_student = mk_user(db_session, "A1125015", role="STUDENT", name="他師學生")

    pending_sch = mk_scholarship(db_session, unit.unit_id, name="待處理獎學金", deadline=datetime.now() + timedelta(days=7))
    draft_sch = mk_scholarship(db_session, unit.unit_id, name="草稿獎學金", deadline=datetime.now() + timedelta(days=8))
    submitted_sch = mk_scholarship(db_session, unit.unit_id, name="已提交獎學金", deadline=datetime.now() + timedelta(days=9))
    due_soon_sch = mk_scholarship(db_session, unit.unit_id, name="即將截止獎學金", deadline=datetime.now() + timedelta(hours=24))
    overdue_sch = mk_scholarship(db_session, unit.unit_id, name="逾期獎學金", deadline=datetime.now() - timedelta(hours=24))
    other_teacher_sch = mk_scholarship(db_session, unit.unit_id, name="他師獎學金", deadline=datetime.now() + timedelta(hours=24))

    pending_app = mk_application(db_session, pending_student.user_id, pending_sch.scholarship_id)
    draft_app = mk_application(db_session, draft_student.user_id, draft_sch.scholarship_id)
    submitted_app = mk_application(db_session, submitted_student.user_id, submitted_sch.scholarship_id)
    due_soon_app = mk_application(db_session, due_soon_student.user_id, due_soon_sch.scholarship_id)
    overdue_app = mk_application(db_session, overdue_student.user_id, overdue_sch.scholarship_id)
    other_teacher_app = mk_application(db_session, other_teacher_student.user_id, other_teacher_sch.scholarship_id)

    mk_recommendation(db_session, application_id=pending_app.application_id, student_id=pending_student.user_id, teacher_id=scenario["teacher_a"].user_id, status="REQUESTED")
    mk_recommendation(db_session, application_id=draft_app.application_id, student_id=draft_student.user_id, teacher_id=scenario["teacher_a"].user_id, status="DRAFT")
    mk_recommendation(db_session, application_id=submitted_app.application_id, student_id=submitted_student.user_id, teacher_id=scenario["teacher_a"].user_id, status="SUBMITTED")
    mk_recommendation(db_session, application_id=due_soon_app.application_id, student_id=due_soon_student.user_id, teacher_id=scenario["teacher_a"].user_id, status="REQUESTED")
    mk_recommendation(db_session, application_id=overdue_app.application_id, student_id=overdue_student.user_id, teacher_id=scenario["teacher_a"].user_id, status="DRAFT")
    mk_recommendation(db_session, application_id=other_teacher_app.application_id, student_id=other_teacher_student.user_id, teacher_id=scenario["teacher_b"].user_id, status="REQUESTED")

    response = client.get(
        "/api/trs/recommendations/teacher/dashboard",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_count"] == 6
    assert payload["pending_count"] == 3
    assert payload["draft_count"] == 2
    assert payload["submitted_count"] == 1
    assert payload["due_soon_count"] == 1
    assert payload["overdue_count"] == 1


def test_invalid_sort_by_does_not_cause_server_error(client, scenario):
    response = client.get(
        "/api/trs/recommendations/teacher",
        headers=auth_headers(scenario["teacher_a"]),
        params={"sort_by": "invalid_field"},
    )

    assert response.status_code == 400


def test_reviewer_cannot_modify_recommendation(client, db_session, scenario):
    reviewer = mk_user(db_session, "reviewer-step4", role="REVIEWER")
    response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(reviewer),
        json={"content": "reviewer 不能改", "submit": False},
    )

    assert response.status_code == 403


def test_submit_creates_notifications_for_reviewers(client, db_session, scenario):
    reviewer = mk_user(db_session, "reviewer-alert", role="REVIEWER", unit_id=scenario["unit"].unit_id)

    response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": "送審內容", "submit": True},
    )

    assert response.status_code == 200
    reviewer_notifications = list(
        db_session.scalars(
            select(Notification).where(Notification.user_id == reviewer.user_id)
        )
    )
    assert reviewer_notifications
    assert any("推薦信已提交" in note.title for note in reviewer_notifications)


def test_due_soon_endpoint_only_admin_can_trigger(client, db_session, scenario):
    admin = mk_user(db_session, "admin-step4", role="ADMIN")
    reviewer = mk_user(db_session, "reviewer-step4-2", role="REVIEWER")

    admin_response = client.post(
        "/api/trs/recommendations/due-soon-notifications",
        headers=auth_headers(admin),
    )
    reviewer_response = client.post(
        "/api/trs/recommendations/due-soon-notifications",
        headers=auth_headers(reviewer),
    )
    teacher_response = client.post(
        "/api/trs/recommendations/due-soon-notifications",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert admin_response.status_code == 200
    assert reviewer_response.status_code == 403
    assert teacher_response.status_code == 403


def test_due_soon_endpoint_creates_teacher_notifications(client, db_session, scenario):
    scenario["scholarship"].deadline = datetime.now() + timedelta(hours=24)
    scenario["rec_a"].status = "REQUESTED"
    db_session.commit()

    admin = mk_user(db_session, "admin-due", role="ADMIN")
    response = client.post(
        "/api/trs/recommendations/due-soon-notifications",
        headers=auth_headers(admin),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["checked_count"] >= 1
    assert payload["created_count"] >= 1

    notes = list(
        db_session.scalars(
            select(Notification).where(Notification.user_id == scenario["teacher_a"].user_id)
        )
    )
    assert any("推薦信即將截止提醒" in note.title for note in notes)


def test_submitted_recommendation_not_in_due_soon_notification(client, db_session, scenario):
    scenario["scholarship"].deadline = datetime.now() + timedelta(hours=24)
    scenario["rec_a"].status = "SUBMITTED"
    db_session.commit()

    admin = mk_user(db_session, "admin-due2", role="ADMIN")
    response = client.post(
        "/api/trs/recommendations/due-soon-notifications",
        headers=auth_headers(admin),
    )
    assert response.status_code == 200

    notes = list(
        db_session.scalars(
            select(Notification).where(Notification.user_id == scenario["teacher_a"].user_id)
        )
    )
    assert all("推薦信即將截止提醒" not in note.title for note in notes)


def test_audit_logs_record_draft_and_submit_without_content(client, db_session, scenario):
    secret_content = "這是一段不應寫入稽核明細的推薦全文"

    draft_response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": secret_content, "submit": False},
    )
    submit_response = client.put(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}",
        headers=auth_headers(scenario["teacher_a"]),
        json={"content": secret_content, "submit": True},
    )

    assert draft_response.status_code == 200
    assert submit_response.status_code == 200

    logs = list(
        db_session.scalars(
            select(AuditLog).where(AuditLog.actor_id == scenario["teacher_a"].user_id)
        )
    )
    actions = {log.action for log in logs}
    assert "TRS_SAVE_DRAFT" in actions
    assert "TRS_SUBMIT_LETTER" in actions
    assert all(secret_content not in (log.detail or "") for log in logs)


def test_view_student_profile_writes_audit_log(client, db_session, scenario):
    response = client.get(
        f"/api/trs/recommendations/{scenario['rec_a'].rec_id}/student-profile",
        headers=auth_headers(scenario["teacher_a"]),
    )

    assert response.status_code == 200
    log = db_session.scalar(
        select(AuditLog).where(
            AuditLog.actor_id == scenario["teacher_a"].user_id,
            AuditLog.action == "TRS_VIEW_STUDENT_PROFILE",
            AuditLog.target_id == scenario["rec_a"].rec_id,
        )
    )
    assert log is not None
