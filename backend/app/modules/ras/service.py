"""RAS — 商業邏輯層（審查與核發，需求書 8.2）。

審查時：本子系統記錄 reviews，並透過 SAS 的 set_application_status()
更新申請狀態，不直接寫 SAS 的資料表。
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ras.models import Review
from app.modules.ras.schemas import ReviewDecision
from app.modules.sas import service as sas_service
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship

DECISION_TO_STATUS = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "NEED_SUPPLEMENT": "NEED_SUPPLEMENT",
}


def list_applications_for_review(db: Session, reviewer: User, scholarship_id: int | None = None) -> list[dict]:
    stmt = (
        select(Application, User.name, User.gpa, Scholarship.name)
        .join(User, Application.student_id == User.user_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
    )
    if scholarship_id is not None:
        stmt = stmt.where(Application.scholarship_id == scholarship_id)
    # 自動排序（NUKSAMS015 簡化版）：GPA 高→低（MySQL 中 NULL 於 DESC 時排最後），再依申請時間
    stmt = stmt.order_by(User.gpa.desc(), Application.created_at.asc())
    rows = db.execute(stmt).all()
    out: list[dict] = []
    for app, student_name, gpa, scholarship_name in rows:
        out.append({
            "application_id": app.application_id,
            "student_id": app.student_id,
            "student_name": student_name,
            "scholarship_id": app.scholarship_id,
            "scholarship_name": scholarship_name,
            "gpa": float(gpa) if gpa is not None else None,
            "status": app.status,
            "statement": app.statement,
            "created_at": app.created_at,
        })
    return out


def decide(db: Session, reviewer: User, application_id: int, data: ReviewDecision) -> dict:
    if data.result not in DECISION_TO_STATUS:
        raise HTTPException(status_code=400, detail="審查結果不正確")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    review = Review(
        application_id=application_id,
        reviewer_id=reviewer.user_id,
        result=data.result,
        comment=data.comment,
    )
    db.add(review)
    # 透過 SAS 介面更新申請狀態（同一交易，最後一起 commit）
    sas_service.set_application_status(db, application_id, DECISION_TO_STATUS[data.result], commit=False)
    db.commit()
    return {"detail": "審查完成", "application_id": application_id, "result": data.result}
