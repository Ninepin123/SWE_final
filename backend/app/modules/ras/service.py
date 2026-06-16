"""RAS — 商業邏輯層（審查與核發，需求書 8.2）。

審查時：寫入 reviews 紀錄（審查人員/結果/時間/意見，item 6），
透過 SAS 介面更新申請狀態，並透過 NCS 通知學生審查結果。
審查清單會帶出最近一次審查紀錄與已送出的推薦信內容。
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ncs import service as ncs_service
from app.modules.ras.models import Review
from app.modules.ras.schemas import ReviewDecision
from app.modules.sas import service as sas_service
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship
from app.modules.trs import service as trs_service

DECISION_TO_STATUS = {"APPROVED": "APPROVED", "REJECTED": "REJECTED", "NEED_SUPPLEMENT": "NEED_SUPPLEMENT"}
RESULT_LABEL = {"APPROVED": "已通過", "REJECTED": "未通過", "NEED_SUPPLEMENT": "需補件"}


def _latest_review(db: Session, application_id: int):
    return db.execute(
        select(Review, User.name)
        .join(User, Review.reviewer_id == User.user_id)
        .where(Review.application_id == application_id)
        .order_by(Review.reviewed_at.desc(), Review.review_id.desc())
        .limit(1)
    ).first()


def list_applications_for_review(db: Session, reviewer: User, scholarship_id: int | None = None) -> list[dict]:
    stmt = (
        select(Application, User.name, User.gpa, Scholarship.name)
        .join(User, Application.student_id == User.user_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
    )
    if scholarship_id is not None:
        stmt = stmt.where(Application.scholarship_id == scholarship_id)
    stmt = stmt.order_by(User.gpa.desc(), Application.created_at.asc())
    rows = db.execute(stmt).all()

    out: list[dict] = []
    for app, student_name, gpa, scholarship_name in rows:
        review_row = _latest_review(db, app.application_id)
        recs = trs_service.get_submitted_for_application(db, app.application_id)
        out.append({
            "application_id": app.application_id,
            "student_id": app.student_id,
            "student_name": student_name,
            "scholarship_id": app.scholarship_id,
            "scholarship_name": scholarship_name,
            "gpa": float(gpa) if gpa is not None else None,
            "status": app.status,
            "statement": app.statement,
            "contact_phone": app.contact_phone,
            "address": app.address,
            "household_status": app.household_status,
            "academic_note": app.academic_note,
            "created_at": app.created_at,
            "reviewer_name": review_row[1] if review_row else None,
            "review_result": review_row[0].result if review_row else None,
            "review_comment": review_row[0].comment if review_row else None,
            "reviewed_at": review_row[0].reviewed_at if review_row else None,
            "recommendations": recs,
        })
    return out


def decide(db: Session, reviewer: User, application_id: int, data: ReviewDecision) -> dict:
    if data.result not in DECISION_TO_STATUS:
        raise HTTPException(status_code=400, detail="審查結果不正確")
    app = db.get(Application, application_id)
    if app is None:
        raise HTTPException(status_code=404, detail="找不到申請案")
    review = Review(
        application_id=application_id, reviewer_id=reviewer.user_id, result=data.result, comment=data.comment
    )
    db.add(review)
    sas_service.set_application_status(db, application_id, DECISION_TO_STATUS[data.result], commit=False)
    db.commit()
    # 通知學生審查結果
    sch = db.get(Scholarship, app.scholarship_id)
    sch_name = sch.name if sch else "獎學金"
    ncs_service.create_notification(
        db, app.student_id, "審查結果通知",
        f"你的「{sch_name}」申請審查結果：{RESULT_LABEL[data.result]}。", commit=True,
    )
    return {"detail": "審查完成", "application_id": application_id, "result": data.result}
