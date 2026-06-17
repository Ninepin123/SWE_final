"""SAS — 商業邏輯層（學生申請與個人資料，需求書 6.2）。

set_application_status() 供 RAS 在審查後更新申請狀態（跨子系統寫入入口）。
申請成功會透過 NCS 發送站內通知。
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ncs import service as ncs_service
from app.modules.sas.models import Application, StudentProfile
from app.modules.sas.schemas import ApplicationCreate, ProfileUpdate
from app.modules.sms.models import Scholarship

VALID_STATUSES = {"UNDER_REVIEW", "NEED_SUPPLEMENT", "APPROVED", "REJECTED"}


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
    }


def apply(db: Session, student: User, data: ApplicationCreate) -> dict:
    sch = db.get(Scholarship, data.scholarship_id)
    if sch is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    if sch.status != "OPEN":
        raise HTTPException(status_code=400, detail="此獎學金已關閉申請")
    dl = _naive(sch.deadline)
    if dl is not None and dl < datetime.now():
        raise HTTPException(status_code=400, detail="已超過申請截止日期")
    if sch.min_gpa is not None and student.gpa is not None and float(student.gpa) < float(sch.min_gpa):
        raise HTTPException(status_code=400, detail=f"GPA 未達申請門檻（需 {sch.min_gpa}）")
    dup = db.scalar(
        select(Application).where(
            Application.student_id == student.user_id, Application.scholarship_id == data.scholarship_id
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="你已申請過此獎學金")
    app = Application(
        student_id=student.user_id,
        scholarship_id=data.scholarship_id,
        status="UNDER_REVIEW",
        statement=data.statement,
        contact_phone=data.contact_phone,
        address=data.address,
        household_status=data.household_status,
        academic_note=data.academic_note,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    ncs_service.create_notification(
        db, student.user_id, "申請已送出", f"你已成功申請「{sch.name}」，目前狀態：審核中。", commit=True
    )
    return _to_out(db, app)


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
        "email": student.email,
        "department": student.department,
        "gpa": float(student.gpa) if student.gpa is not None else None,
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
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    return get_profile(db, student)
