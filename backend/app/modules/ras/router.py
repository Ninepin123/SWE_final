"""RAS 審查與核發 — API 路由
需求書：Chapter 8，功能需求 8.2.1–8.2.8
v1 範圍：審查人員查看申請案（含 GPA 自動排序）、做出通過/不通過/補件決定。
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
    reviewer: User = Depends(require_roles("REVIEWER", "ADMIN")),
):
    """查詢待審查的申請案，預設依 GPA 由高到低排序（8.2.1 / 8.2.3）。"""
    return service.list_applications_for_review(db, reviewer, scholarship_id)


@router.post("/applications/{application_id}/decision")
def decide(
    application_id: int,
    body: ReviewDecision,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER", "ADMIN")),
):
    """對申請案做出審查決定（通過/不通過/要求補件，8.2.4）。"""
    return service.decide(db, reviewer, application_id, body)
