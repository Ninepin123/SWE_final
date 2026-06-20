"""TRS — 商業邏輯層（教師推薦，需求書 7.2）。

隱私（7.2.5）：推薦信內容僅老師本人與審查人員可讀；學生只能看到狀態。
"""
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import asc, case, desc, func, or_, select
from sqlalchemy.orm import Session

from app.modules.aas import service as aas_service
from app.modules.aas.models import Unit, User
from app.modules.aas.security import hash_password
from app.modules.ncs import service as ncs_service
from app.modules.ras.models import Review
from app.modules.sas.models import Application, ApplicationDocument, StudentProfile
from app.modules.sms.models import Scholarship
from app.modules.trs.models import Recommendation
from app.modules.trs.schemas import RecommendationLetterUpdate, RecommendationRequestCreate

STATUS_LABEL = {"REQUESTED": "已邀請", "DRAFT": "撰寫中", "SUBMITTED": "已送出"}
PENDING_STATUSES = {"REQUESTED", "PENDING"}
VALID_STATUSES = {"REQUESTED", "PENDING", "DRAFT", "SUBMITTED"}
VALID_SORT_FIELDS = {"deadline", "submitted_at", "created_at", "student_name", "scholarship_name", "status"}
VALID_ORDER = {"asc", "desc"}
DEV_QUICK_LOGIN_TRS_ACCOUNT_PREFIX = "DEVTRS"
TRS_REVIEWER_SUBMITTED_TITLE = "推薦信已提交"
TRS_DUE_SOON_TITLE = "推薦信即將截止提醒"


def _scholarship_name_for_app(db: Session, application_id: int) -> str | None:
    app = db.get(Application, application_id)
    if app is None:
        return None
    sch = db.get(Scholarship, app.scholarship_id)
    return sch.name if sch else None


def _scholarship_deadline_for_app(db: Session, application_id: int):
    app = db.get(Application, application_id)
    if app is None:
        return None
    sch = db.get(Scholarship, app.scholarship_id)
    return sch.deadline if sch else None


def ensure_teacher_owns_recommendation(db: Session, rec_id: int, teacher: User) -> Recommendation:
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="找不到推薦案")
    if rec.teacher_id != teacher.user_id:
        raise HTTPException(status_code=403, detail="只能查看或編輯指派給你的推薦信")
    return rec


def _teacher_recommendation_base_query(teacher: User):
    submitted_at_expr = case(
        (Recommendation.status == "SUBMITTED", Recommendation.updated_at),
        else_=None,
    )
    return (
        select(
            Recommendation,
            User.name.label("student_name"),
            User.account.label("student_account"),
            Scholarship.name.label("scholarship_name"),
            Scholarship.deadline.label("deadline"),
            submitted_at_expr.label("submitted_at"),
        )
        .join(User, Recommendation.student_id == User.user_id)
        .join(Application, Recommendation.application_id == Application.application_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .where(Recommendation.teacher_id == teacher.user_id)
    )


def _resolve_teacher_sort_expression(sort_by: str):
    submitted_at_expr = case(
        (Recommendation.status == "SUBMITTED", Recommendation.updated_at),
        else_=None,
    )
    mapping = {
        "deadline": Scholarship.deadline,
        "submitted_at": submitted_at_expr,
        "created_at": Recommendation.created_at,
        "student_name": User.name,
        "scholarship_name": Scholarship.name,
        "status": Recommendation.status,
    }
    return mapping[sort_by]


def _reviewer_targets_for_application(db: Session, application: Application) -> list[User]:
    # 優先：若已有審查紀錄，通知該申請曾參與審查的 reviewer。
    reviewer_ids = list(
        db.scalars(
            select(Review.reviewer_id)
            .where(Review.application_id == application.application_id)
            .distinct()
        )
    )
    if reviewer_ids:
        return list(
            db.scalars(
                select(User)
                .where(
                    User.user_id.in_(reviewer_ids),
                    User.role == "REVIEWER",
                    User.status == "ACTIVE",
                )
            )
        )

    scholarship = db.get(Scholarship, application.scholarship_id)
    stmt = select(User).where(User.role == "REVIEWER", User.status == "ACTIVE")
    if scholarship and scholarship.unit_id is not None:
        stmt = stmt.where(User.unit_id == scholarship.unit_id)
    return list(db.scalars(stmt.order_by(User.user_id.asc())))


def _due_soon_recommendation_rows(db: Session, now: datetime, upper_bound: datetime):
    return db.execute(
        select(Recommendation, Scholarship, Application, User)
        .join(Application, Recommendation.application_id == Application.application_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .join(User, Recommendation.teacher_id == User.user_id)
        .where(
            Recommendation.status != "SUBMITTED",
            Scholarship.deadline.is_not(None),
            Scholarship.deadline >= now,
            Scholarship.deadline <= upper_bound,
            User.status == "ACTIVE",
        )
        .order_by(Scholarship.deadline.asc(), Recommendation.rec_id.asc())
    ).all()


def ensure_dev_teacher_recommendations(db: Session, teacher: User, count: int = 6) -> int:
    """開發用：快速登入教師時，補齊可測試的推薦邀請資料。"""
    if teacher.role != "TEACHER" or count <= 0:
        return 0

    now = datetime.now()
    created_count = 0
    for index in range(1, count + 1):
        student_account = f"{DEV_QUICK_LOGIN_TRS_ACCOUNT_PREFIX}{index:02d}"
        scholarship_name = f"TRS 快速測試獎學金 {index}"

        student = db.scalar(select(User).where(User.account == student_account))
        if student is None:
            student = User(
                account=student_account,
                password=hash_password("password123"),
                name=f"TRS 測試學生 {index}",
                email=f"devtrs{index:02d}@nuk.edu.tw",
                role="STUDENT",
                department="資訊工程學系",
                gpa=3.50,
                status="ACTIVE",
            )
            db.add(student)
            db.flush()

        scholarship = db.scalar(select(Scholarship).where(Scholarship.name == scholarship_name))
        if scholarship is None:
            default_unit = db.scalar(select(Unit).order_by(Unit.unit_id.asc()))
            if default_unit is None:
                default_unit = Unit(name="TRS 開發測試單位", type="SCHOOL", contact_email="trs-dev@nuk.edu.tw")
                db.add(default_unit)
                db.flush()

            sponsor = db.scalar(
                select(User)
                .where(User.role == "SPONSOR", User.status == "ACTIVE")
                .order_by(User.user_id.asc())
            )
            scholarship = Scholarship(
                unit_id=(sponsor.unit_id if sponsor and sponsor.unit_id else default_unit.unit_id),
                name=scholarship_name,
                year=now.year,
                amount=12000 + (index * 500),
                quota=10,
                min_gpa=2.50,
                category="SCHOOL",
                description="開發模式快速登入測試資料。",
                deadline=now + timedelta(days=3 + index),
                status="OPEN",
                created_by=sponsor.user_id if sponsor else teacher.user_id,
            )
            db.add(scholarship)
            db.flush()

        application = db.scalar(
            select(Application).where(
                Application.student_id == student.user_id,
                Application.scholarship_id == scholarship.scholarship_id,
            )
        )
        if application is None:
            application = Application(
                student_id=student.user_id,
                scholarship_id=scholarship.scholarship_id,
                status="UNDER_REVIEW",
                statement="快速登入測試用申請案。",
                submitted_at=now,
            )
            db.add(application)
            db.flush()

        existing_rec = db.scalar(
            select(Recommendation).where(
                Recommendation.application_id == application.application_id,
                Recommendation.teacher_id == teacher.user_id,
            )
        )
        if existing_rec is None:
            db.add(
                Recommendation(
                    application_id=application.application_id,
                    student_id=student.user_id,
                    teacher_id=teacher.user_id,
                    status="REQUESTED",
                    content=None,
                )
            )
            created_count += 1

    if created_count:
        db.commit()
    return created_count


def request_recommendation(db: Session, student: User, data: RecommendationRequestCreate) -> dict:
    app = db.get(Application, data.application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    if app.student_id != student.user_id:
        raise HTTPException(status_code=403, detail="只能為自己的申請邀請推薦")
    teacher = db.get(User, data.teacher_id)
    if teacher is None or teacher.role != "TEACHER":
        raise HTTPException(status_code=400, detail="指定的老師不存在")
    dup = db.scalar(
        select(Recommendation).where(
            Recommendation.application_id == data.application_id, Recommendation.teacher_id == data.teacher_id
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="已邀請過這位老師")
    rec = Recommendation(
        application_id=data.application_id, student_id=student.user_id, teacher_id=data.teacher_id, status="REQUESTED"
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    sch_name = _scholarship_name_for_app(db, data.application_id)
    ncs_service.create_notification(
        db, teacher.user_id, "新的推薦邀請",
        f"學生 {student.name} 邀請你為其「{sch_name}」申請撰寫推薦信。", commit=True,
    )
    return {
        "rec_id": rec.rec_id,
        "application_id": rec.application_id,
        "student_id": rec.student_id,
        "teacher_id": rec.teacher_id,
        "scholarship_name": sch_name,
        "teacher_name": teacher.name,
        "status": rec.status,
        "submitted_at": None,
        "updated_at": rec.updated_at,
    }


def list_for_teacher(
    db: Session,
    teacher: User,
    keyword: str | None = None,
    status: str | None = None,
    sort_by: str = "deadline",
    order: str = "asc",
) -> list[dict]:
    normalized_status = status.strip().upper() if status else None
    normalized_sort = (sort_by or "deadline").strip().lower()
    normalized_order = (order or "asc").strip().lower()

    if normalized_status and normalized_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="推薦狀態不存在")
    if normalized_sort not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=400, detail="排序欄位不存在")
    if normalized_order not in VALID_ORDER:
        raise HTTPException(status_code=400, detail="排序方向不存在")

    stmt = _teacher_recommendation_base_query(teacher)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                User.name.ilike(pattern),
                User.account.ilike(pattern),
                Scholarship.name.ilike(pattern),
            )
        )
    if normalized_status:
        stmt = stmt.where(Recommendation.status == normalized_status)

    sort_expr = _resolve_teacher_sort_expression(normalized_sort)
    ordering = asc(sort_expr) if normalized_order == "asc" else desc(sort_expr)
    secondary = desc(Recommendation.updated_at)
    rows = db.execute(stmt.order_by(ordering, secondary)).all()
    return [
        {
            "rec_id": rec.rec_id,
            "application_id": rec.application_id,
            "student_id": rec.student_id,
            "teacher_id": rec.teacher_id,
            "student_name": student_name,
            "student_account": student_account,
            "scholarship_name": scholarship_name,
            "deadline": deadline,
            "content": rec.content,
            "status": rec.status,
            "submitted_at": submitted_at,
            "updated_at": rec.updated_at,
        }
        for rec, student_name, student_account, scholarship_name, deadline, submitted_at in rows
    ]


def save_letter(db: Session, teacher: User, rec_id: int, data: RecommendationLetterUpdate) -> dict:
    rec = ensure_teacher_owns_recommendation(db, rec_id, teacher)
    if rec.status == "SUBMITTED":
        raise HTTPException(status_code=409, detail="Submitted recommendation cannot be modified")
    previous_status = rec.status
    if data.content is not None:
        rec.content = data.content
    rec.status = "SUBMITTED" if data.submit else "DRAFT"
    db.commit()
    db.refresh(rec)
    student_user = db.get(User, rec.student_id)

    application = db.get(Application, rec.application_id)
    scholarship = db.get(Scholarship, application.scholarship_id) if application else None
    scholarship_name = scholarship.name if scholarship else _scholarship_name_for_app(db, rec.application_id)

    if data.submit:
        ncs_service.create_notification(
            db, rec.student_id, "推薦信已送出", f"{teacher.name} 老師已送出你的推薦信。", commit=True
        )
        reviewer_targets = _reviewer_targets_for_application(db, application) if application else []
        student_name = student_user.name if student_user else f"學生#{rec.student_id}"
        for reviewer in reviewer_targets:
            body = (
                f"教師 {teacher.name} 已提交學生 {student_name} 的推薦信，"
                f"獎學金：{scholarship_name or '-'}，rec_id={rec.rec_id}。"
            )
            ncs_service.create_notification_if_absent(
                db,
                user_id=reviewer.user_id,
                title=TRS_REVIEWER_SUBMITTED_TITLE,
                body=body,
                commit=False,
            )
        db.commit()

        aas_service.write_audit(
            db,
            actor_id=teacher.user_id,
            action="TRS_SUBMIT_LETTER",
            target_type="recommendation",
            target_id=rec.rec_id,
            detail=(
                f"Teacher submitted recommendation rec_id={rec.rec_id} "
                f"application_id={rec.application_id} from_status={previous_status}"
            ),
        )
    else:
        aas_service.write_audit(
            db,
            actor_id=teacher.user_id,
            action="TRS_SAVE_DRAFT",
            target_type="recommendation",
            target_id=rec.rec_id,
            detail=(
                f"Teacher saved recommendation draft rec_id={rec.rec_id} "
                f"application_id={rec.application_id} from_status={previous_status}"
            ),
        )

    return {
        "rec_id": rec.rec_id,
        "application_id": rec.application_id,
        "student_id": rec.student_id,
        "teacher_id": rec.teacher_id,
        "student_name": student_user.name if student_user else None,
        "scholarship_name": scholarship_name,
        "deadline": _scholarship_deadline_for_app(db, rec.application_id),
        "content": rec.content,
        "status": rec.status,
        "submitted_at": rec.updated_at if rec.status == "SUBMITTED" else None,
        "updated_at": rec.updated_at,
    }


def get_student_profile_for_recommendation(db: Session, teacher: User, rec_id: int) -> dict:
    rec = ensure_teacher_owns_recommendation(db, rec_id, teacher)
    application = db.get(Application, rec.application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="找不到申請案")

    student = db.get(User, rec.student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="找不到學生資料")

    scholarship = db.get(Scholarship, application.scholarship_id)
    if scholarship is None:
        raise HTTPException(status_code=404, detail="找不到獎學金資料")

    profile = db.get(StudentProfile, rec.student_id)
    documents = list(
        db.scalars(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application.application_id)
            .order_by(ApplicationDocument.document_id.asc())
        )
    )

    aas_service.write_audit(
        db,
        actor_id=teacher.user_id,
        action="TRS_VIEW_STUDENT_PROFILE",
        target_type="recommendation",
        target_id=rec.rec_id,
        detail=f"Teacher viewed student profile for rec_id={rec.rec_id} application_id={rec.application_id}",
    )

    return {
        "rec_id": rec.rec_id,
        "application_id": rec.application_id,
        "status": rec.status,
        "student": {
            "user_id": student.user_id,
            "name": student.name,
            "account": student.account,
            "email": student.email,
        },
        "profile": None if profile is None else {
            "grade": profile.grade,
            "identity_type": profile.identity_type,
            "contact_email": profile.contact_email,
            "contact_phone": profile.contact_phone,
            "address": profile.address,
            "emergency_contact_name": profile.emergency_contact_name,
            "emergency_contact_phone": profile.emergency_contact_phone,
        },
        "application": {
            "application_id": application.application_id,
            "status": application.status,
            "submitted_at": application.submitted_at,
        },
        "scholarship": {
            "scholarship_id": scholarship.scholarship_id,
            "name": scholarship.name,
            "deadline": scholarship.deadline,
        },
        "documents": [
            {
                "document_id": document.document_id,
                "document_type": document.document_type,
                "title": document.title,
                "content_text": document.content_text,
            }
            for document in documents
        ],
    }


def get_teacher_dashboard(db: Session, teacher: User) -> dict:
    now = datetime.now()
    due_soon_deadline = now + timedelta(hours=48)
    rows = db.execute(
        select(Recommendation.status, Scholarship.deadline)
        .join(Application, Recommendation.application_id == Application.application_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .where(Recommendation.teacher_id == teacher.user_id)
    ).all()

    total_count = len(rows)
    pending_count = sum(1 for status, _ in rows if status in PENDING_STATUSES)
    draft_count = sum(1 for status, _ in rows if status == "DRAFT")
    submitted_count = sum(1 for status, _ in rows if status == "SUBMITTED")
    due_soon_count = sum(
        1
        for status, deadline in rows
        if status != "SUBMITTED" and deadline is not None and now <= deadline <= due_soon_deadline
    )
    overdue_count = sum(
        1
        for status, deadline in rows
        if status != "SUBMITTED" and deadline is not None and deadline < now
    )

    return {
        "total_count": total_count,
        "pending_count": pending_count,
        "draft_count": draft_count,
        "submitted_count": submitted_count,
        "due_soon_count": due_soon_count,
        "overdue_count": overdue_count,
    }


def list_for_student(db: Session, student: User) -> list[dict]:
    rows = db.execute(
        select(Recommendation, User.name, Scholarship.name, Scholarship.deadline)
        .join(User, Recommendation.teacher_id == User.user_id)
        .join(Application, Recommendation.application_id == Application.application_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .where(Recommendation.student_id == student.user_id)
        .order_by(Recommendation.updated_at.desc())
    ).all()
    # 注意：不回傳 content（隱私）
    return [
        {
            "rec_id": rec.rec_id,
            "application_id": rec.application_id,
            "teacher_id": rec.teacher_id,
            "scholarship_name": scholarship_name,
            "teacher_name": teacher_name,
            "status": rec.status,
            "deadline": deadline,
            "submitted_at": rec.updated_at if rec.status == "SUBMITTED" else None,
            "updated_at": rec.updated_at,
        }
        for rec, teacher_name, scholarship_name, deadline in rows
    ]


def get_submitted_for_application(db: Session, application_id: int) -> list[dict]:
    """供 RAS 審查時讀取已送出的推薦信內容。"""
    rows = db.execute(
        select(Recommendation, User.name)
        .join(User, Recommendation.teacher_id == User.user_id)
        .where(Recommendation.application_id == application_id, Recommendation.status == "SUBMITTED")
    ).all()
    return [{"teacher_name": teacher_name, "content": rec.content} for rec, teacher_name in rows]


def get_recommendations_for_reviewer(db: Session, application_id: int, reviewer: User) -> list[dict]:
    """Reviewer 只能看到已提交推薦信內容；未提交僅回狀態。"""
    rows = db.execute(
        select(Recommendation, User.name)
        .join(User, Recommendation.teacher_id == User.user_id)
        .where(Recommendation.application_id == application_id)
        .order_by(Recommendation.updated_at.desc(), Recommendation.rec_id.desc())
    ).all()

    result: list[dict] = []
    viewed_submitted = False
    for rec, teacher_name in rows:
        is_submitted = rec.status == "SUBMITTED"
        result.append(
            {
                "rec_id": rec.rec_id,
                "teacher_name": teacher_name,
                "status": rec.status,
                "content": rec.content if is_submitted else None,
                "content_available": is_submitted,
            }
        )
        viewed_submitted = viewed_submitted or is_submitted

    if viewed_submitted:
        aas_service.write_audit(
            db,
            actor_id=reviewer.user_id,
            action="TRS_VIEW_SUBMITTED_LETTER",
            target_type="application",
            target_id=application_id,
            detail=f"Reviewer viewed submitted recommendation(s) for application_id={application_id}",
        )
    return result


def create_due_soon_notifications(db: Session, triggered_by: User | None = None, hours: int = 48) -> dict:
    now = datetime.now()
    upper_bound = now + timedelta(hours=hours)
    rows = _due_soon_recommendation_rows(db, now=now, upper_bound=upper_bound)

    created_count = 0
    checked_count = len(rows)
    for rec, scholarship, application, teacher in rows:
        deadline_text = scholarship.deadline.strftime("%Y-%m-%d %H:%M") if scholarship.deadline else "-"
        title = TRS_DUE_SOON_TITLE
        body = (
            f"你負責的推薦案件即將截止：{scholarship.name}，"
            f"deadline={deadline_text}，rec_id={rec.rec_id}，application_id={application.application_id}。"
        )
        created = ncs_service.create_notification_if_absent(
            db,
            user_id=teacher.user_id,
            title=title,
            body=body,
            commit=False,
        )
        if created is not None:
            created_count += 1

    if created_count:
        db.commit()

    aas_service.write_audit(
        db,
        actor_id=triggered_by.user_id if triggered_by else None,
        action="TRS_DUE_SOON_NOTIFICATION",
        target_type="recommendation",
        target_id=None,
        detail=f"checked={checked_count}, created={created_count}, within_hours={hours}",
    )
    return {"checked_count": checked_count, "created_count": created_count}
