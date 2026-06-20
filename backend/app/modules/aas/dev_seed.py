"""AAS — 開發用種子資料（一次性、可重複執行）。

建立示範單位、各角色帳號與兩筆示範獎學金，方便團隊立刻試跑 v1 流程。
（為了讓密碼用與登入相同的 bcrypt 雜湊，種子改用 Python 撰寫而非 SQL。）

用法（先啟動過一次 start.bat 讓資料表建好，再於 backend 目錄、venv 啟用後執行）：
    Windows:  .venv\\Scripts\\python -m app.modules.aas.dev_seed
    macOS/Linux: python -m app.modules.aas.dev_seed

所有帳號的密碼皆為： password123
"""
from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.database import SessionLocal
from app.modules.aas.models import Unit, User
from app.modules.aas.security import hash_password
from app.modules.ncs.models import Notification
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship
from app.modules.trs.models import Recommendation

DEMO_PASSWORD = "password123"


def _get_or_create_unit(db, name, type_, email):
    unit = db.scalar(select(Unit).where(Unit.name == name))
    if unit:
        return unit
    unit = Unit(name=name, type=type_, contact_email=email)
    db.add(unit)
    db.flush()
    return unit


def _get_or_create_user(db, account, name, role, **extra):
    user = db.scalar(select(User).where(User.account == account))
    if user:
        return user
    user = User(
        account=account,
        password=hash_password(DEMO_PASSWORD),
        name=name,
        role=role,
        status="ACTIVE",
        **extra,
    )
    db.add(user)
    db.flush()
    return user


def _ensure_scholarship(db, name, **fields):
    scholarship = db.scalar(select(Scholarship).where(Scholarship.name == name))
    if scholarship:
        return scholarship
    scholarship = Scholarship(name=name, **fields)
    db.add(scholarship)
    db.flush()
    return scholarship


def _get_or_create_application(db, student_id, scholarship_id, status="UNDER_REVIEW"):
    application = db.scalar(
        select(Application).where(
            Application.student_id == student_id,
            Application.scholarship_id == scholarship_id,
        )
    )
    if application:
        return application
    application = Application(
        student_id=student_id,
        scholarship_id=scholarship_id,
        status=status,
        statement="開發種子資料建立的示範申請案。",
        submitted_at=datetime.now(),
    )
    db.add(application)
    db.flush()
    return application


def _ensure_recommendation(db, application_id, student_id, teacher_id, status, content=None):
    recommendation = db.scalar(
        select(Recommendation).where(
            Recommendation.application_id == application_id,
            Recommendation.teacher_id == teacher_id,
        )
    )
    if recommendation is None:
        recommendation = Recommendation(
            application_id=application_id,
            student_id=student_id,
            teacher_id=teacher_id,
            status=status,
            content=content,
        )
        db.add(recommendation)
        db.flush()
    else:
        recommendation.status = status
        recommendation.content = content
    return recommendation


def _ensure_notification(db, user_id, title, body):
    exists = db.scalar(
        select(Notification.notification_id).where(
            Notification.user_id == user_id,
            Notification.title == title,
            Notification.body == body,
        )
    )
    if exists:
        return
    db.add(Notification(user_id=user_id, title=title, body=body, is_read=False))


def main():
    db = SessionLocal()
    try:
        osa = _get_or_create_unit(db, "學生事務處生活輔導組", "SCHOOL", "osa@nuk.edu.tw")
        moe = _get_or_create_unit(db, "教育部", "GOVERNMENT", "moe@example.gov.tw")

        _get_or_create_user(db, "admin", "系統管理員", "ADMIN", email="admin@nuk.edu.tw")
        sponsor = _get_or_create_user(db, "sponsor", "生輔組承辦人", "SPONSOR", email="sponsor@nuk.edu.tw", unit_id=osa.unit_id)
        reviewer = _get_or_create_user(db, "reviewer", "審查委員", "REVIEWER", email="reviewer@nuk.edu.tw", unit_id=osa.unit_id)
        _get_or_create_user(db, "reviewer2", "第二審查委員", "REVIEWER", email="reviewer2@nuk.edu.tw", unit_id=osa.unit_id)
        teacher_a = _get_or_create_user(db, "teacher", "陳老師", "TEACHER", email="teacher@nuk.edu.tw")
        teacher_b = _get_or_create_user(db, "teacher2", "李老師", "TEACHER", email="teacher2@nuk.edu.tw")
        student_a = _get_or_create_user(db, "A1125529", "黃文傑", "STUDENT", email="student1@nuk.edu.tw", gpa=3.85, department="資訊工程學系")
        student_b = _get_or_create_user(db, "A1125599", "王小明", "STUDENT", email="student2@nuk.edu.tw", gpa=3.20, department="電機工程學系")
        db.flush()

        now = datetime.now()
        sch_relief = _ensure_scholarship(
            db, "清寒優秀學生獎學金",
            unit_id=osa.unit_id, year=2026, amount=20000, quota=5, min_gpa=3.50,
            category="LOW_INCOME", description="提供家境清寒且學業成績優良之在學學生申請。",
            deadline=now + timedelta(hours=30),
            status="OPEN", created_by=sponsor.user_id,
        )
        sch_moe = _ensure_scholarship(
            db, "教育部學產基金助學金",
            unit_id=moe.unit_id, year=2026, amount=15000, quota=10, min_gpa=None,
            category="GOVERNMENT", description="教育部提供之助學金，不限 GPA。",
            deadline=now + timedelta(days=7),
            status="OPEN", created_by=sponsor.user_id,
        )

        sch_overdue = _ensure_scholarship(
            db,
            "TRS 逾期測試獎學金",
            unit_id=osa.unit_id,
            year=2026,
            amount=10000,
            quota=5,
            min_gpa=2.5,
            category="SCHOOL",
            description="開發測試：逾期未提交推薦信案件。",
            deadline=now - timedelta(hours=12),
            status="OPEN",
            created_by=sponsor.user_id,
        )

        app_a1 = _get_or_create_application(db, student_a.user_id, sch_relief.scholarship_id)
        app_a2 = _get_or_create_application(db, student_a.user_id, sch_moe.scholarship_id)
        app_b1 = _get_or_create_application(db, student_b.user_id, sch_moe.scholarship_id)
        app_b2 = _get_or_create_application(db, student_b.user_id, sch_overdue.scholarship_id)

        _ensure_recommendation(
            db,
            app_a1.application_id,
            student_a.user_id,
            teacher_a.user_id,
            status="REQUESTED",
            content=None,
        )
        _ensure_recommendation(
            db,
            app_a2.application_id,
            student_a.user_id,
            teacher_a.user_id,
            status="DRAFT",
            content="這是開發用草稿推薦信內容。",
        )
        _ensure_recommendation(
            db,
            app_b1.application_id,
            student_b.user_id,
            teacher_a.user_id,
            status="SUBMITTED",
            content="學生具備良好學習態度與研究潛力，特此推薦。",
        )
        _ensure_recommendation(
            db,
            app_b2.application_id,
            student_b.user_id,
            teacher_b.user_id,
            status="REQUESTED",
            content=None,
        )

        _ensure_notification(
            db,
            teacher_a.user_id,
            "推薦信即將截止提醒",
            f"你負責的推薦案件即將截止：{sch_relief.name}，請盡速提交。",
        )
        _ensure_notification(
            db,
            reviewer.user_id,
            "推薦信已提交",
            f"教師 {teacher_a.name} 已提交學生 {student_b.name} 的推薦信，請進入審查系統查看。",
        )

        db.commit()
        print("✅ 示範資料建立完成。")
        print("   可用帳號（密碼皆為 password123）：")
        print("   - admin     系統管理員")
        print("   - sponsor   獎助單位（可新增獎學金）")
        print("   - reviewer  審查人員（可審查申請）")
        print("   - reviewer2 第二審查人員")
        print("   - teacher   老師")
        print("   - teacher2  老師")
        print("   - A1125529  學生（GPA 3.85）")
        print("   - A1125599  學生（GPA 3.20）")
        print("   已建立 TRS 測試推薦案件：REQUESTED / DRAFT / SUBMITTED / 逾期未提交")
    finally:
        db.close()


if __name__ == "__main__":
    main()
