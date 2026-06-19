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
from app.modules.sas.models import Application, ApplicationDocument, StudentProfile
from app.modules.sas.schemas import (
    ApplicationCreate,
    ApplicationDocumentWrite,
    ApplicationUpdate,
    ProfileUpdate,
)
from app.modules.sms.models import Scholarship

VALID_STATUSES = {"DRAFT", "UNDER_REVIEW", "NEED_SUPPLEMENT", "APPROVED", "REJECTED"}
VALID_CATEGORIES = {"SCHOOL", "GOVERNMENT", "PRIVATE", "LOW_INCOME", "MERIT", "OTHER"}
VALID_DOCUMENT_TYPES = {"TRANSCRIPT", "AUTOBIOGRAPHY", "CERTIFICATE", "OTHER"}


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
    db.commit()
    db.refresh(app)
    return _to_out(db, app)


def get_my_application(db: Session, student: User, application_id: int) -> dict:
    return _to_out(db, _get_owned_application(db, student, application_id))


def update_draft(db: Session, student: User, application_id: int, data: ApplicationUpdate) -> dict:
    app = _get_owned_application(db, student, application_id)
    _ensure_editable(db, app)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(app, key, value)
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
    else:
        document.title = data.title.strip()
        document.content_text = content
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
    db.delete(document)
    db.commit()


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
    db.commit()
    db.refresh(app)
    ncs_service.create_notification(
        db,
        student.user_id,
        "申請已送出",
        f"你已成功申請「{scholarship.name}」，目前狀態：審核中。",
        commit=True,
    )
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
    app.status = new_status
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
