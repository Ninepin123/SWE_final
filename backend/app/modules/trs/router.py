"""TRS 教師推薦 — API 路由
需求書：Chapter 7。範圍：學生邀請老師推薦、老師撰寫/送出推薦信、學生查看推薦狀態。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.trs import service
from app.modules.trs.schemas import (
    RecommendationLetterUpdate,
    RecommendationRequestCreate,
    RecommendationStudentOut,
    RecommendationTeacherOut,
)

router = APIRouter(prefix="/api/trs", tags=["TRS 教師推薦"])


@router.post("/recommendations", response_model=RecommendationStudentOut, status_code=status.HTTP_201_CREATED)
def request_recommendation(
    body: RecommendationRequestCreate, db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))
):
    """學生為自己的申請邀請一位老師撰寫推薦信。"""
    return service.request_recommendation(db, student, body)


@router.get("/recommendations/student", response_model=list[RecommendationStudentOut])
def my_recommendations(db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))):
    """學生查看自己各申請的推薦狀態（看不到內容）。"""
    return service.list_for_student(db, student)


@router.get("/recommendations/teacher", response_model=list[RecommendationTeacherOut])
def teacher_recommendations(db: Session = Depends(get_db), teacher: User = Depends(require_roles("TEACHER"))):
    """老師查看被指派的推薦邀請（含已寫內容）。"""
    return service.list_for_teacher(db, teacher)


@router.put("/recommendations/{rec_id}", response_model=RecommendationTeacherOut)
def save_letter(
    rec_id: int,
    body: RecommendationLetterUpdate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("TEACHER")),
):
    """老師存草稿或送出推薦信。"""
    return service.save_letter(db, teacher, rec_id, body)
