"""TRS — 商業邏輯層（教師推薦，需求書 7.2）。

隱私（7.2.5）：推薦信內容僅老師本人與審查人員可讀；學生只能看到狀態。
"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.ncs import service as ncs_service
from app.modules.sas.models import Application
from app.modules.sms.models import Scholarship
from app.modules.trs.models import Recommendation
from app.modules.trs.schemas import RecommendationLetterUpdate, RecommendationRequestCreate

STATUS_LABEL = {"REQUESTED": "已邀請", "DRAFT": "撰寫中", "SUBMITTED": "已送出"}


def _scholarship_name_for_app(db: Session, application_id: int) -> str | None:
    app = db.get(Application, application_id)
    if app is None:
        return None
    sch = db.get(Scholarship, app.scholarship_id)
    return sch.name if sch else None


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
        "scholarship_name": sch_name,
        "teacher_name": teacher.name,
        "status": rec.status,
        "updated_at": rec.updated_at,
    }


def list_for_teacher(db: Session, teacher: User) -> list[dict]:
    rows = db.execute(
        select(Recommendation, User.name, Scholarship.name)
        .join(User, Recommendation.student_id == User.user_id)
        .join(Application, Recommendation.application_id == Application.application_id)
        .join(Scholarship, Application.scholarship_id == Scholarship.scholarship_id)
        .where(Recommendation.teacher_id == teacher.user_id)
        .order_by(Recommendation.updated_at.desc())
    ).all()
    return [
        {
            "rec_id": rec.rec_id,
            "application_id": rec.application_id,
            "student_name": student_name,
            "scholarship_name": scholarship_name,
            "content": rec.content,
            "status": rec.status,
            "updated_at": rec.updated_at,
        }
        for rec, student_name, scholarship_name in rows
    ]


def save_letter(db: Session, teacher: User, rec_id: int, data: RecommendationLetterUpdate) -> dict:
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="找不到推薦案")
    if rec.teacher_id != teacher.user_id:
        raise HTTPException(status_code=403, detail="只能編輯指派給你的推薦信")
    if data.content is not None:
        rec.content = data.content
    rec.status = "SUBMITTED" if data.submit else "DRAFT"
    db.commit()
    db.refresh(rec)
    if data.submit:
        ncs_service.create_notification(
            db, rec.student_id, "推薦信已送出", f"{teacher.name} 老師已送出你的推薦信。", commit=True
        )
    return {
        "rec_id": rec.rec_id,
        "application_id": rec.application_id,
        "student_name": None,
        "scholarship_name": _scholarship_name_for_app(db, rec.application_id),
        "content": rec.content,
        "status": rec.status,
        "updated_at": rec.updated_at,
    }


def list_for_student(db: Session, student: User) -> list[dict]:
    rows = db.execute(
        select(Recommendation, User.name, Scholarship.name)
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
            "scholarship_name": scholarship_name,
            "teacher_name": teacher_name,
            "status": rec.status,
            "updated_at": rec.updated_at,
        }
        for rec, teacher_name, scholarship_name in rows
    ]


def get_submitted_for_application(db: Session, application_id: int) -> list[dict]:
    """供 RAS 審查時讀取已送出的推薦信內容。"""
    rows = db.execute(
        select(Recommendation, User.name)
        .join(User, Recommendation.teacher_id == User.user_id)
        .where(Recommendation.application_id == application_id, Recommendation.status == "SUBMITTED")
    ).all()
    return [{"teacher_name": teacher_name, "content": rec.content} for rec, teacher_name in rows]
