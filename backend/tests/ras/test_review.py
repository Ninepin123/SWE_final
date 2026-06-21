"""RAS 審查與核發 — 功能測試（對應需求書 Ch.8 / 缺失清單 RAS001-032）。

涵蓋：自動排序(GPA)、單位審查存取限制、通過/不通過決議與通知、
核發名單、年度統計與報表、CSV 匯出、角色權限。
使用 in-memory SQLite，與既有 AAS / SAS 測試同一套 fixture 模式。
"""
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
from app.modules.ras.router import router
from app.modules.sas.models import (
    Application,
    ApplicationDocument,
    ApplicationEvent,
    StudentProfile,
    SupplementRequest,
)
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
            AuditLog.__table__,
            Scholarship.__table__,
            Application.__table__,
            ApplicationDocument.__table__,
            ApplicationEvent.__table__,
            SupplementRequest.__table__,
            StudentProfile.__table__,
            Notification.__table__,
            Recommendation.__table__,
            Review.__table__,
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


# ---- helpers ----

def mk_unit(db, name):
    unit = Unit(name=name, type="COLLEGE")
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def mk_user(db, account, *, role="STUDENT", unit_id=None, gpa=None, department=None):
    user = User(
        account=account,
        password=hash_password("password123"),
        name=account,
        role=role,
        unit_id=unit_id,
        gpa=gpa,
        department=department,
        status="ACTIVE",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def mk_scholarship(db, *, unit_id, name, year=2026, amount=10000):
    s = Scholarship(
        unit_id=unit_id,
        name=name,
        year=year,
        amount=amount,
        quota=5,
        category="MERIT",
        deadline=datetime.now() + timedelta(days=30),
        status="OPEN",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def mk_application(db, *, student_id, scholarship_id, status="UNDER_REVIEW"):
    a = Application(student_id=student_id, scholarship_id=scholarship_id, status=status)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def mk_recommendation(db, *, application_id, student_id, teacher_id, status="REQUESTED", content=None):
    recommendation = Recommendation(
        application_id=application_id,
        student_id=student_id,
        teacher_id=teacher_id,
        status=status,
        content=content,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


def auth(user):
    return {"Authorization": f"Bearer {create_access_token(user.user_id, user.role)}"}


@pytest.fixture()
def scenario(db_session):
    """兩個單位、各自的審查人員與申請案，供大多數測試共用。"""
    db = db_session
    unit_a = mk_unit(db, "理學院")
    unit_b = mk_unit(db, "工學院")

    reviewer_a = mk_user(db, "reviewerA", role="REVIEWER", unit_id=unit_a.unit_id)
    reviewer_b = mk_user(db, "reviewerB", role="REVIEWER", unit_id=unit_b.unit_id)

    sch_a = mk_scholarship(db, unit_id=unit_a.unit_id, name="理學院菁英獎", amount=10000)
    sch_b = mk_scholarship(db, unit_id=unit_b.unit_id, name="工學院菁英獎", amount=20000)

    stu_high = mk_user(db, "stuHigh", gpa=3.95, department="物理系")
    stu_low = mk_user(db, "stuLow", gpa=3.10, department="化學系")
    stu_b = mk_user(db, "stuB", gpa=3.50, department="電機系")

    app_high = mk_application(db, student_id=stu_high.user_id, scholarship_id=sch_a.scholarship_id)
    app_low = mk_application(db, student_id=stu_low.user_id, scholarship_id=sch_a.scholarship_id)
    app_b = mk_application(db, student_id=stu_b.user_id, scholarship_id=sch_b.scholarship_id)

    return dict(
        reviewer_a=reviewer_a, reviewer_b=reviewer_b,
        sch_a=sch_a, sch_b=sch_b,
        stu_high=stu_high, stu_low=stu_low, stu_b=stu_b,
        app_high=app_high, app_low=app_low, app_b=app_b,
    )


# ---- RAS007-008：自動排序 / Ranking ----

def test_applications_sorted_by_gpa_desc(client, scenario):
    r = client.get("/api/ras/applications", params={"sort_by": "gpa_desc"}, headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    rows = r.json()
    # 單位隔離後 reviewerA 只看到自己單位的 2 件，且依 GPA 由高到低
    gpas = [row["gpa"] for row in rows]
    assert gpas == sorted(gpas, reverse=True)
    assert rows[0]["student_name"] == "stuHigh"
    assert rows[-1]["student_name"] == "stuLow"


def test_applications_sorted_by_gpa_asc(client, scenario):
    r = client.get("/api/ras/applications", params={"sort_by": "gpa_asc"}, headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    rows = r.json()
    assert rows[0]["student_name"] == "stuLow"
    assert rows[-1]["student_name"] == "stuHigh"


# ---- RAS018-019：單位審查存取限制 ----

def test_unit_isolation_reviewer_sees_only_own_unit(client, scenario):
    r_a = client.get("/api/ras/applications", headers=auth(scenario["reviewer_a"]))
    r_b = client.get("/api/ras/applications", headers=auth(scenario["reviewer_b"]))
    names_a = {row["student_name"] for row in r_a.json()}
    names_b = {row["student_name"] for row in r_b.json()}
    assert names_a == {"stuHigh", "stuLow"}      # 理學院
    assert names_b == {"stuB"}                    # 工學院
    assert names_a.isdisjoint(names_b)


# ---- 角色權限：非審查人員不可進入審查 ----

def test_non_reviewer_cannot_list_applications(client, db_session):
    student = mk_user(db_session, "someStudent", role="STUDENT")
    r = client.get("/api/ras/applications", headers=auth(student))
    assert r.status_code == 403


# ---- 通過 / 不通過 決議 + 通知 ----

def test_decide_approve_records_review_and_notifies(client, db_session, scenario):
    reviewer = scenario["reviewer_a"]
    app_high = scenario["app_high"]

    r = client.post(
        f"/api/ras/applications/{app_high.application_id}/decision",
        json={"result": "APPROVED", "comment": "表現優異"},
        headers=auth(reviewer),
    )
    assert r.status_code == 200
    assert r.json()["result"] == "APPROVED"

    # 申請狀態更新為 APPROVED
    db_session.expire_all()
    assert db_session.get(Application, app_high.application_id).status == "APPROVED"

    # 審查紀錄寫入（審查人員 / 結果 / 意見）
    review = db_session.scalar(select(Review).where(Review.application_id == app_high.application_id))
    assert review is not None
    assert review.result == "APPROVED"
    assert review.reviewer_id == reviewer.user_id
    assert review.comment == "表現優異"

    # 學生收到審查結果通知
    note = db_session.scalar(select(Notification).where(Notification.user_id == scenario["stu_high"].user_id))
    assert note is not None
    assert "審查結果" in note.title

    # 列表會帶出最近一次審查紀錄
    rows = client.get("/api/ras/applications", headers=auth(reviewer)).json()
    high = next(row for row in rows if row["application_id"] == app_high.application_id)
    assert high["review_result"] == "APPROVED"
    assert high["reviewer_name"] == reviewer.name


def test_decide_reject_sets_status_rejected(client, db_session, scenario):
    app_low = scenario["app_low"]
    r = client.post(
        f"/api/ras/applications/{app_low.application_id}/decision",
        json={"result": "REJECTED", "comment": "資格不符"},
        headers=auth(scenario["reviewer_a"]),
    )
    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.get(Application, app_low.application_id).status == "REJECTED"


def test_decide_need_supplement_creates_request(client, db_session, scenario):
    app_high = scenario["app_high"]
    deadline = (datetime.now() + timedelta(days=7)).isoformat()

    r = client.post(
        f"/api/ras/applications/{app_high.application_id}/decision",
        json={
            "result": "NEED_SUPPLEMENT",
            "comment": "請補交財力證明",
            "supplement_deadline": deadline,
        },
        headers=auth(scenario["reviewer_a"]),
    )

    assert r.status_code == 200
    db_session.expire_all()
    assert db_session.get(Application, app_high.application_id).status == "NEED_SUPPLEMENT"

    request = db_session.scalar(
        select(SupplementRequest).where(
            SupplementRequest.application_id == app_high.application_id
        )
    )
    assert request is not None
    assert request.required_items == "請補交財力證明"
    assert request.reviewer_id == scenario["reviewer_a"].user_id


def test_decide_invalid_result_is_rejected(client, scenario):
    r = client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "MAYBE"},
        headers=auth(scenario["reviewer_a"]),
    )
    assert r.status_code == 400


def test_reviewer_can_view_submitted_recommendation_content(client, db_session, scenario):
    teacher = mk_user(db_session, "teacher-submitted", role="TEACHER")
    mk_recommendation(
        db_session,
        application_id=scenario["app_high"].application_id,
        student_id=scenario["stu_high"].user_id,
        teacher_id=teacher.user_id,
        status="SUBMITTED",
        content="這是已提交推薦信內容",
    )

    response = client.get("/api/ras/applications", headers=auth(scenario["reviewer_a"]))
    assert response.status_code == 200
    target = next(item for item in response.json() if item["application_id"] == scenario["app_high"].application_id)
    assert target["recommendations"]
    assert target["recommendations"][0]["status"] == "SUBMITTED"
    assert target["recommendations"][0]["content"] == "這是已提交推薦信內容"
    assert target["recommendations"][0]["content_available"] is True


def test_reviewer_cannot_view_draft_recommendation_content(client, db_session, scenario):
    teacher = mk_user(db_session, "teacher-draft", role="TEACHER")
    mk_recommendation(
        db_session,
        application_id=scenario["app_high"].application_id,
        student_id=scenario["stu_high"].user_id,
        teacher_id=teacher.user_id,
        status="DRAFT",
        content="草稿內容不可給 reviewer",
    )

    response = client.get("/api/ras/applications", headers=auth(scenario["reviewer_a"]))
    assert response.status_code == 200
    target = next(item for item in response.json() if item["application_id"] == scenario["app_high"].application_id)
    assert target["recommendations"]
    draft_item = next(item for item in target["recommendations"] if item["status"] == "DRAFT")
    assert draft_item["content"] is None
    assert draft_item["content_available"] is False


# ---- RAS014-015：核發名單 ----

def test_award_list_contains_only_approved(client, db_session, scenario):
    # 通過 stuHigh、駁回 stuLow
    client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "APPROVED"}, headers=auth(scenario["reviewer_a"]),
    )
    client.post(
        f"/api/ras/applications/{scenario['app_low'].application_id}/decision",
        json={"result": "REJECTED"}, headers=auth(scenario["reviewer_a"]),
    )

    r = client.get("/api/ras/award-list", headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    awards = r.json()
    assert len(awards) == 1
    item = awards[0]
    assert item["student_name"] == "stuHigh"
    assert item["amount"] == 10000
    assert item["year"] == 2026
    assert item["status"] == "APPROVED"
    assert item["department"] == "物理系"


# ---- RAS016-017：年度統計與報表 ----

def test_annual_statistics(client, scenario):
    client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "APPROVED"}, headers=auth(scenario["reviewer_a"]),
    )
    client.post(
        f"/api/ras/applications/{scenario['app_low'].application_id}/decision",
        json={"result": "REJECTED"}, headers=auth(scenario["reviewer_a"]),
    )

    r = client.get("/api/ras/statistics", params={"year": 2026}, headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    stats = r.json()
    assert stats["total_winners"] == 1
    assert stats["total_amount"] == 10000
    # reviewerA 受單位隔離，僅見理學院
    assert len(stats["unit_stats"]) == 1
    unit = stats["unit_stats"][0]
    assert unit["unit_name"] == "理學院"
    assert unit["total_applications"] == 2
    assert unit["approved_count"] == 1
    assert unit["pass_rate"] == 50.0


# ---- RAS016：CSV 匯出 ----

def test_statistics_export_csv(client, scenario):
    client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "APPROVED"}, headers=auth(scenario["reviewer_a"]),
    )
    r = client.get("/api/ras/statistics/export", params={"year": 2026}, headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    body = r.content.decode("utf-8-sig")  # 去掉 Excel BOM
    assert "學號" in body and "姓名" in body
    assert "stuHigh" in body
    assert "理學院" in body


def test_statistics_export_overall_totals_are_accumulated(client, scenario):
    """回歸：匯出 CSV 的【總體統計】須反映已核發人數與金額（先前恆為 0）。"""
    client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "APPROVED"}, headers=auth(scenario["reviewer_a"]),
    )
    client.post(
        f"/api/ras/applications/{scenario['app_low'].application_id}/decision",
        json={"result": "REJECTED"}, headers=auth(scenario["reviewer_a"]),
    )
    r = client.get("/api/ras/statistics/export", params={"year": 2026}, headers=auth(scenario["reviewer_a"]))
    body = r.content.decode("utf-8-sig")
    lines = [ln.strip() for ln in body.splitlines()]
    assert "總計核發人數,1" in lines
    assert "通過比例,50.0%" in lines       # 2 件中 1 件通過
    assert "總計核發金額,10000" in lines


# ---- RAS016-017：PDF 匯出 ----

def test_statistics_export_pdf(client, scenario):
    client.post(
        f"/api/ras/applications/{scenario['app_high'].application_id}/decision",
        json={"result": "APPROVED"}, headers=auth(scenario["reviewer_a"]),
    )
    r = client.get("/api/ras/statistics/export/pdf", params={"year": 2026}, headers=auth(scenario["reviewer_a"]))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers["content-disposition"]
    # 有效的 PDF 檔頭，且內容非空（已嵌入字型與表格）
    assert r.content[:5] == b"%PDF-"
    assert len(r.content) > 1500


def test_statistics_export_pdf_requires_reviewer_or_admin(client, db_session):
    student = mk_user(db_session, "plainStudent", role="STUDENT")
    r = client.get("/api/ras/statistics/export/pdf", headers=auth(student))
    assert r.status_code == 403
