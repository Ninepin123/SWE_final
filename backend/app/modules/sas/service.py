"""SAS — 商業邏輯層（學生申請與個人資料，需求書 6.2）。

set_application_status() 供 RAS 在審查後更新申請狀態（跨子系統寫入入口）。
申請成功會透過 NCS 發送站內通知。
"""
from datetime import datetime

from fastapi import HTTPException
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.aas.models import Unit, User
from app.modules.ncs import service as ncs_service
from app.modules.sas.models import (
    Application,
    ApplicationDocument,
    ApplicationEvent,
    StudentProfile,
    SupplementRequest,
)
from app.modules.sas.schemas import (
    ApplicationCreate,
    ApplicationDocumentWrite,
    ApplicationUpdate,
    ProfileUpdate,
    SupplementRequestCreate,
    SupplementSubmit,
)
from app.modules.sms.models import Scholarship

VALID_STATUSES = {"DRAFT", "UNDER_REVIEW", "NEED_SUPPLEMENT", "APPROVED", "REJECTED"}
VALID_CATEGORIES = {"SCHOOL", "GOVERNMENT", "PRIVATE", "LOW_INCOME", "MERIT", "OTHER"}
VALID_DOCUMENT_TYPES = {"TRANSCRIPT", "AUTOBIOGRAPHY", "CERTIFICATE", "OTHER"}


def write_application_event(
    db: Session,
    application_id: int,
    actor_id: int | None,
    event_type: str,
    from_status: str | None = None,
    to_status: str | None = None,
    detail: str | None = None,
    commit: bool = False,
) -> ApplicationEvent:
    event = ApplicationEvent(
        application_id=application_id,
        actor_id=actor_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        detail=detail,
    )
    db.add(event)
    if commit:
        db.commit()
    return event


def _naive(dt: datetime | None) -> datetime | None:
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def _to_out(db: Session, app: Application) -> dict:
    sch = db.get(Scholarship, app.scholarship_id)
    return {
        "application_id": app.application_id,
        "scholarship_id": app.scholarship_id,
        "scholarship_name": sch.name if sch else None,
        "status": app.status,
        "statement": app.statement,
        "contact_phone": app.contact_phone,
        "address": app.address,
        "household_status": app.household_status,
        "academic_note": app.academic_note,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
        "submitted_at": app.submitted_at,
        "can_edit": app.status == "DRAFT" and not _is_deadline_passed(sch),
    }


def _allowed_departments(value: str | None) -> list[str]:
    if not value or value.strip() in {"不限", "不限科系", "ALL"}:
        return []
    return [item.strip() for item in re.split(r"[,，、;/]", value) if item.strip()]


def _eligibility_reasons(
    scholarship: Scholarship,
    student: User,
    remaining_quota: int,
    already_applied: bool,
    now: datetime,
) -> list[str]:
    reasons: list[str] = []
    if scholarship.status != "OPEN":
        reasons.append("獎學金目前未開放申請")
    deadline = _naive(scholarship.deadline)
    if deadline is not None and deadline < now:
        reasons.append("已超過申請截止時間")
    if remaining_quota <= 0:
        reasons.append("申請名額已滿")
    if scholarship.min_gpa is not None:
        if student.gpa is None:
            reasons.append("個人資料缺少 GPA")
        elif float(student.gpa) < float(scholarship.min_gpa):
            reasons.append(f"GPA 未達門檻（需 {float(scholarship.min_gpa):g}）")
    departments = _allowed_departments(scholarship.department_limit)
    if departments:
        if not student.department:
            reasons.append("個人資料缺少科系")
        elif student.department not in departments:
            reasons.append("科系不符合申請資格")
    if already_applied:
        reasons.append("已申請過此獎學金")
    return reasons


def list_scholarships_for_student(
    db: Session,
    student: User,
    keyword: str | None = None,
    category: str | None = None,
    department: str | None = None,
    deadline_before: datetime | None = None,
    eligible_only: bool = False,
) -> list[dict]:
    if category and category not in VALID_CATEGORIES:
        raise HTTPException(status_code=400, detail="分類不存在")

    stmt = select(Scholarship, Unit).join(Unit, Scholarship.unit_id == Unit.unit_id)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            Scholarship.name.ilike(pattern)
            | Scholarship.description.ilike(pattern)
            | Unit.name.ilike(pattern)
        )
    if category:
        stmt = stmt.where(Scholarship.category == category)
    if deadline_before is not None:
        stmt = stmt.where(Scholarship.deadline <= _naive(deadline_before))
    stmt = stmt.order_by(Scholarship.deadline.asc(), Scholarship.created_at.desc())

    requested_department = department.strip() if department else None
    now = datetime.now()
    result: list[dict] = []
    for scholarship, unit in db.execute(stmt).all():
        departments = _allowed_departments(scholarship.department_limit)
        if requested_department and departments and requested_department not in departments:
            continue

        application_count = db.scalar(
            select(func.count(Application.application_id)).where(
                Application.scholarship_id == scholarship.scholarship_id,
                Application.status != "DRAFT",
            )
        ) or 0
        remaining_quota = max(scholarship.quota - application_count, 0)
        already_applied = db.scalar(
            select(Application.application_id).where(
                Application.scholarship_id == scholarship.scholarship_id,
                Application.student_id == student.user_id,
            )
        ) is not None
        reasons = _eligibility_reasons(
            scholarship,
            student,
            remaining_quota,
            already_applied,
            now,
        )
        if eligible_only and reasons:
            continue
        result.append(
            {
                "scholarship_id": scholarship.scholarship_id,
                "name": scholarship.name,
                "year": scholarship.year,
                "amount": scholarship.amount,
                "quota": scholarship.quota,
                "remaining_quota": remaining_quota,
                "min_gpa": float(scholarship.min_gpa) if scholarship.min_gpa is not None else None,
                "department_limit": scholarship.department_limit,
                "category": scholarship.category,
                "description": scholarship.description,
                "deadline": scholarship.deadline,
                "status": scholarship.status,
                "unit_id": scholarship.unit_id,
                "unit_name": unit.name,
                "contact_email": unit.contact_email,
                "required_documents": [],
                "already_applied": already_applied,
                "can_apply": not reasons,
                "ineligibility_reasons": reasons,
            }
        )
    return result


def _is_deadline_passed(scholarship: Scholarship | None) -> bool:
    if scholarship is None:
        return True
    deadline = _naive(scholarship.deadline)
    return deadline is not None and deadline < datetime.now()


def _get_eligible_scholarship(db: Session, student: User, scholarship_id: int) -> Scholarship:
    sch = db.get(Scholarship, scholarship_id)
    if sch is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    application_count = db.scalar(
        select(func.count(Application.application_id)).where(
            Application.scholarship_id == scholarship_id,
            Application.status != "DRAFT",
        )
    ) or 0
    reasons = _eligibility_reasons(
        sch,
        student,
        max(sch.quota - application_count, 0),
        False,
        datetime.now(),
    )
    if reasons:
        raise HTTPException(status_code=400, detail="；".join(reasons))
    return sch


def _get_owned_application(db: Session, student: User, application_id: int) -> Application:
    app = db.get(Application, application_id)
    if app is None or app.student_id != student.user_id:
        raise HTTPException(status_code=404, detail="找不到申請案")
    return app


def _ensure_editable(db: Session, app: Application) -> Scholarship:
    if app.status != "DRAFT":
        raise HTTPException(status_code=409, detail="申請已正式送出，無法再修改")
    scholarship = db.get(Scholarship, app.scholarship_id)
    if _is_deadline_passed(scholarship):
        raise HTTPException(status_code=409, detail="已超過申請截止時間，草稿已鎖定")
    if scholarship is None or scholarship.status != "OPEN":
        raise HTTPException(status_code=409, detail="獎學金目前未開放申請")
    return scholarship


def create_draft(db: Session, student: User, data: ApplicationCreate) -> dict:
    sch = _get_eligible_scholarship(db, student, data.scholarship_id)
    dup = db.scalar(
        select(Application).where(
            Application.student_id == student.user_id,
            Application.scholarship_id == data.scholarship_id,
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="此獎學金已有申請或草稿")
    app = Application(
        student_id=student.user_id,
        scholarship_id=sch.scholarship_id,
        status="DRAFT",
        statement=data.statement,
        contact_phone=data.contact_phone,
        address=data.address,
        household_status=data.household_status,
        academic_note=data.academic_note,
    )
    db.add(app)
    db.flush()
    write_application_event(
        db,
        app.application_id,
        student.user_id,
        "DRAFT_CREATED",
        to_status="DRAFT",
        detail="建立申請草稿",
    )
    db.commit()
    db.refresh(app)
    return _to_out(db, app)


def get_my_application(db: Session, student: User, application_id: int) -> dict:
    return _to_out(db, _get_owned_application(db, student, application_id))


def list_application_events(
    db: Session,
    student: User,
    application_id: int,
) -> list[dict]:
    _get_owned_application(db, student, application_id)
    rows = db.execute(
        select(ApplicationEvent, User.name, User.role)
        .join(User, ApplicationEvent.actor_id == User.user_id, isouter=True)
        .where(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.created_at.asc(), ApplicationEvent.event_id.asc())
    ).all()
    return [
        {
            "event_id": event.event_id,
            "application_id": event.application_id,
            "actor_id": event.actor_id,
            "actor_name": actor_name,
            "actor_role": actor_role,
            "event_type": event.event_type,
            "from_status": event.from_status,
            "to_status": event.to_status,
            "detail": event.detail,
            "created_at": event.created_at,
        }
        for event, actor_name, actor_role in rows
    ]


def update_draft(db: Session, student: User, application_id: int, data: ApplicationUpdate) -> dict:
    app = _get_owned_application(db, student, application_id)
    _ensure_editable(db, app)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(app, key, value)
    write_application_event(
        db,
        application_id,
        student.user_id,
        "DRAFT_UPDATED",
        from_status="DRAFT",
        to_status="DRAFT",
        detail="更新申請草稿",
    )
    db.commit()
    db.refresh(app)
    return _to_out(db, app)


def list_documents(db: Session, student: User, application_id: int) -> list[ApplicationDocument]:
    _get_owned_application(db, student, application_id)
    return list(
        db.scalars(
            select(ApplicationDocument)
            .where(ApplicationDocument.application_id == application_id)
            .order_by(ApplicationDocument.document_id)
        )
    )


def save_text_document(
    db: Session,
    student: User,
    application_id: int,
    data: ApplicationDocumentWrite,
) -> ApplicationDocument:
    app = _get_owned_application(db, student, application_id)
    _ensure_editable(db, app)
    if data.document_type not in VALID_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="文件類型不存在")
    content = data.content_text.strip()
    if not content:
        raise HTTPException(status_code=400, detail="文件內容不可為空")
    document = db.scalar(
        select(ApplicationDocument).where(
            ApplicationDocument.application_id == application_id,
            ApplicationDocument.document_type == data.document_type,
        )
    )
    if document is None:
        document = ApplicationDocument(
            application_id=application_id,
            document_type=data.document_type,
            title=data.title.strip(),
            content_text=content,
        )
        db.add(document)
        event_type = "DOCUMENT_CREATED"
    else:
        document.title = data.title.strip()
        document.content_text = content
        event_type = "DOCUMENT_UPDATED"
    write_application_event(
        db,
        application_id,
        student.user_id,
        event_type,
        from_status=app.status,
        to_status=app.status,
        detail=f"文字文件：{data.title.strip()}",
    )
    db.commit()
    db.refresh(document)
    return document


def delete_document(
    db: Session,
    student: User,
    application_id: int,
    document_id: int,
) -> None:
    app = _get_owned_application(db, student, application_id)
    _ensure_editable(db, app)
    document = db.get(ApplicationDocument, document_id)
    if document is None or document.application_id != application_id:
        raise HTTPException(status_code=404, detail="找不到文件")
    title = document.title
    db.delete(document)
    write_application_event(
        db,
        application_id,
        student.user_id,
        "DOCUMENT_DELETED",
        from_status=app.status,
        to_status=app.status,
        detail=f"刪除文字文件：{title}",
    )
    db.commit()


def _supplement_to_out(request: SupplementRequest) -> dict:
    return {
        "supplement_id": request.supplement_id,
        "application_id": request.application_id,
        "reviewer_id": request.reviewer_id,
        "required_items": request.required_items,
        "deadline": request.deadline,
        "status": request.status,
        "response_text": request.response_text,
        "created_at": request.created_at,
        "submitted_at": request.submitted_at,
        "can_submit": (
            request.status == "REQUESTED"
            and _naive(request.deadline) >= datetime.now()
        ),
    }


def create_supplement_request(
    db: Session,
    reviewer: User,
    application_id: int,
    data: SupplementRequestCreate,
) -> dict:
    app = db.get(Application, application_id)
    if app is None or app.status not in {"UNDER_REVIEW", "NEED_SUPPLEMENT"}:
        raise HTTPException(status_code=409, detail="此申請案目前不可要求補件")
    scholarship = db.get(Scholarship, app.scholarship_id)
    if (
        reviewer.unit_id is None
        or scholarship is None
        or reviewer.unit_id != scholarship.unit_id
    ):
        raise HTTPException(status_code=403, detail="只能處理自己單位的申請案")
    deadline = _naive(data.deadline)
    if deadline <= datetime.now():
        raise HTTPException(status_code=400, detail="補件期限必須晚於目前時間")
    active = db.scalar(
        select(SupplementRequest).where(
            SupplementRequest.application_id == application_id,
            SupplementRequest.status == "REQUESTED",
        )
    )
    if active is not None:
        raise HTTPException(status_code=409, detail="此申請案已有待處理的補件要求")
    request = SupplementRequest(
        application_id=application_id,
        reviewer_id=reviewer.user_id,
        required_items=data.required_items.strip(),
        deadline=deadline,
        status="REQUESTED",
    )
    previous_status = app.status
    app.status = "NEED_SUPPLEMENT"
    db.add(request)
    db.flush()
    write_application_event(
        db,
        application_id,
        reviewer.user_id,
        "SUPPLEMENT_REQUESTED",
        from_status=previous_status,
        to_status="NEED_SUPPLEMENT",
        detail=request.required_items,
    )
    db.commit()
    db.refresh(request)
    ncs_service.create_notification(
        db,
        app.student_id,
        "補件通知",
        f"你的申請需要補件：{request.required_items}。期限：{deadline.isoformat(sep=' ', timespec='minutes')}",
        commit=True,
    )
    return _supplement_to_out(request)


def list_supplement_requests(
    db: Session,
    student: User,
    application_id: int,
) -> list[dict]:
    _get_owned_application(db, student, application_id)
    requests = db.scalars(
        select(SupplementRequest)
        .where(SupplementRequest.application_id == application_id)
        .order_by(SupplementRequest.created_at.desc(), SupplementRequest.supplement_id.desc())
    ).all()
    return [_supplement_to_out(request) for request in requests]


def submit_supplement(
    db: Session,
    student: User,
    application_id: int,
    supplement_id: int,
    data: SupplementSubmit,
) -> dict:
    app = _get_owned_application(db, student, application_id)
    request = db.get(SupplementRequest, supplement_id)
    if request is None or request.application_id != application_id:
        raise HTTPException(status_code=404, detail="找不到補件要求")
    if request.status != "REQUESTED":
        raise HTTPException(status_code=409, detail="此補件已送出")
    if _naive(request.deadline) < datetime.now():
        raise HTTPException(status_code=409, detail="已超過補件期限")
    request.response_text = data.response_text.strip()
    request.status = "SUBMITTED"
    request.submitted_at = datetime.now()
    app.status = "UNDER_REVIEW"
    write_application_event(
        db,
        application_id,
        student.user_id,
        "SUPPLEMENT_SUBMITTED",
        from_status="NEED_SUPPLEMENT",
        to_status="UNDER_REVIEW",
        detail="學生已提交補件內容",
    )
    db.commit()
    db.refresh(request)
    ncs_service.create_notification(
        db,
        request.reviewer_id,
        "學生已完成補件",
        f"申請案 #{application_id} 已提交補件內容。",
        commit=True,
    )
    return _supplement_to_out(request)


def submit_application(db: Session, student: User, application_id: int) -> dict:
    app = _get_owned_application(db, student, application_id)
    scholarship = _ensure_editable(db, app)
    _get_eligible_scholarship(db, student, scholarship.scholarship_id)
    missing: list[str] = []
    required_fields = {
        "statement": "申請理由",
        "contact_phone": "聯絡電話",
        "address": "通訊地址",
        "household_status": "家庭狀況",
    }
    for field, label in required_fields.items():
        value = getattr(app, field)
        if value is None or not str(value).strip():
            missing.append(label)
    if missing:
        raise HTTPException(status_code=400, detail=f"申請資料不完整：{ '、'.join(missing) }")
    document_count = db.scalar(
        select(func.count(ApplicationDocument.document_id)).where(
            ApplicationDocument.application_id == application_id,
            func.length(func.trim(ApplicationDocument.content_text)) > 0,
        )
    ) or 0
    if document_count == 0:
        raise HTTPException(status_code=400, detail="請至少提交一份文字文件")
    app.status = "UNDER_REVIEW"
    app.submitted_at = datetime.now()
    write_application_event(
        db,
        application_id,
        student.user_id,
        "APPLICATION_SUBMITTED",
        from_status="DRAFT",
        to_status="UNDER_REVIEW",
        detail="正式送出申請",
    )
    ncs_service.create_notification(
        db,
        student.user_id,
        "申請已送出",
        f"你已成功申請「{scholarship.name}」，目前狀態：審核中。",
        commit=False,
    )
    reviewers = db.scalars(
        select(User).where(
            User.unit_id == scholarship.unit_id,
            User.role.in_(("SPONSOR", "REVIEWER")),
            User.status == "ACTIVE",
        )
    ).all()
    for reviewer in reviewers:
        ncs_service.create_notification(
            db,
            reviewer.user_id,
            "收到新的獎學金申請",
            f"「{scholarship.name}」收到來自 {student.name} 的申請案 #{application_id}。",
            commit=False,
        )
    db.commit()
    db.refresh(app)
    return _to_out(db, app)


def apply(db: Session, student: User, data: ApplicationCreate) -> dict:
    """相容舊呼叫：建立草稿後立即送出。"""
    draft = create_draft(db, student, data)
    return submit_application(db, student, draft["application_id"])


def list_my_applications(db: Session, student: User) -> list[dict]:
    apps = db.scalars(
        select(Application).where(Application.student_id == student.user_id).order_by(Application.created_at.desc())
    ).all()
    return [_to_out(db, a) for a in apps]


def set_application_status(db: Session, application_id: int, new_status: str, commit: bool = True) -> Application:
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="狀態不存在")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    old_status = app.status
    app.status = new_status
    write_application_event(
        db,
        application_id,
        None,
        "STATUS_CHANGED",
        from_status=old_status,
        to_status=new_status,
        detail="系統更新申請狀態",
    )
    if commit:
        db.commit()
    return app


def get_profile(db: Session, student: User) -> dict:
    profile = db.get(StudentProfile, student.user_id)
    return {
        "user_id": student.user_id,
        "account": student.account,
        "name": student.name,
        "department": student.department,
        "grade": profile.grade if profile else None,
        "gpa": float(student.gpa) if student.gpa is not None else None,
        "identity_type": profile.identity_type if profile else None,
        "email": (profile.contact_email if profile and profile.contact_email is not None else student.email),
        "contact_phone": profile.contact_phone if profile else None,
        "address": profile.address if profile else None,
        "emergency_contact_name": profile.emergency_contact_name if profile else None,
        "emergency_contact_phone": profile.emergency_contact_phone if profile else None,
    }


def update_profile(db: Session, student: User, data: ProfileUpdate) -> dict:
    profile = db.get(StudentProfile, student.user_id)
    if profile is None:
        profile = StudentProfile(user_id=student.user_id)
        db.add(profile)
    payload = data.model_dump(exclude_unset=True)
    if "email" in payload:
        profile.contact_email = payload.pop("email")
    for key, value in payload.items():
        setattr(profile, key, value)
    db.commit()
    return get_profile(db, student)
