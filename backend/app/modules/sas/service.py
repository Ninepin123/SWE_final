"""SAS — 商業邏輯層（學生申請，需求書 6.2）。

set_application_status() 是提供給 RAS（審查子系統）更新申請狀態的介面：
跨子系統「寫入」一律透過對方 service 函式，不直接寫別人的資料表。
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.sas.models import Application
from app.modules.sas.schemas import ApplicationCreate
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
        "created_at": app.created_at,
    }


def apply(db: Session, student: User, data: ApplicationCreate) -> dict:
    sch = db.get(Scholarship, data.scholarship_id)
    if sch is None:
        raise HTTPException(status_code=404, detail="找不到獎學金")
    # 申請截止/關閉檢查（NUKSAMS007 / NUKSAMS008）
    if sch.status != "OPEN":
        raise HTTPException(status_code=400, detail="此獎學金已關閉申請")
    dl = _naive(sch.deadline)
    if dl is not None and dl < datetime.now():
        raise HTTPException(status_code=400, detail="已超過申請截止日期")
    # GPA 門檻（若獎學金有設且學生有 GPA）
    if sch.min_gpa is not None and student.gpa is not None and float(student.gpa) < float(sch.min_gpa):
        raise HTTPException(status_code=400, detail=f"GPA 未達申請門檻（需 {sch.min_gpa}）")
    # 不可重複申請同一獎學金
    dup = db.scalar(
        select(Application).where(
            Application.student_id == student.user_id,
            Application.scholarship_id == data.scholarship_id,
        )
    )
    if dup is not None:
        raise HTTPException(status_code=409, detail="你已申請過此獎學金")
    app = Application(
        student_id=student.user_id,
        scholarship_id=data.scholarship_id,
        status="UNDER_REVIEW",
        statement=data.statement,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return _to_out(db, app)


def list_my_applications(db: Session, student: User) -> list[dict]:
    apps = db.scalars(
        select(Application)
        .where(Application.student_id == student.user_id)
        .order_by(Application.created_at.desc())
    ).all()
    return [_to_out(db, a) for a in apps]


def set_application_status(db: Session, application_id: int, new_status: str, commit: bool = True) -> Application:
    """供 RAS 在審查後更新申請狀態（跨子系統寫入入口）。"""
    if new_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="狀態不存在")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    app.status = new_status
    if commit:
        db.commit()
    return app
