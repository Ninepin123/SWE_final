"""RAS 審查與核發 — API 路由
需求書：Chapter 8。範圍：審查人員查看申請案（GPA 排序、含推薦信與審查紀錄）、做出審查決定。
注意：依需求僅「審查單位 / 審查人員(REVIEWER)」可審查（管理員不參與審查）。
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.ras import service
from app.modules.ras.schemas import ReviewApplicationOut, ReviewDecision

router = APIRouter(prefix="/api/ras", tags=["RAS 審查與核發"])


@router.get("/applications", response_model=list[ReviewApplicationOut])
def list_applications(
    scholarship_id: int | None = None,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.list_applications_for_review(db, reviewer, scholarship_id)


@router.post("/applications/{application_id}/decision")
def decide(
    application_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.decide(db, reviewer, application_id, body)
