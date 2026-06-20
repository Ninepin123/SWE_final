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
    DueSoonNotificationRunOut,
    RecommendationLetterUpdate,
    RecommendationRequestCreate,
    TeacherRecommendationDashboardOut,
    RecommendationStudentOut,
    RecommendationStudentProfileOut,
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
def teacher_recommendations(
    keyword: str | None = None,
    status: str | None = None,
    sort_by: str = "deadline",
    order: str = "asc",
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("TEACHER")),
):
    """老師查看被指派的推薦邀請（含已寫內容）。"""
    return service.list_for_teacher(db, teacher, keyword=keyword, status=status, sort_by=sort_by, order=order)


@router.get("/recommendations/teacher/dashboard", response_model=TeacherRecommendationDashboardOut)
def teacher_recommendation_dashboard(
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("TEACHER")),
):
    """老師查看自己負責推薦案件的統計摘要。"""
    return service.get_teacher_dashboard(db, teacher)


@router.put("/recommendations/{rec_id}", response_model=RecommendationTeacherOut)
def save_letter(
    rec_id: int,
    body: RecommendationLetterUpdate,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("TEACHER")),
):
    """老師存草稿或送出推薦信。"""
    return service.save_letter(db, teacher, rec_id, body)


@router.get("/recommendations/{rec_id}/student-profile", response_model=RecommendationStudentProfileOut)
def recommendation_student_profile(
    rec_id: int,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("TEACHER")),
):
    """老師查看自己負責推薦案件的學生與申請資料。"""
    return service.get_student_profile_for_recommendation(db, teacher, rec_id)


@router.post("/recommendations/due-soon-notifications", response_model=DueSoonNotificationRunOut)
def trigger_due_soon_notifications(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles("ADMIN")),
):
    """管理員手動觸發：48 小時內截止且未提交推薦案提醒。"""
    return service.create_due_soon_notifications(db, triggered_by=admin)
