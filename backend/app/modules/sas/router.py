"""SAS 學生申請 — API 路由
需求書：Chapter 6，功能需求 6.2.1–6.2.7
v1 範圍：學生線上申請獎學金、查詢自己的申請進度。
（可申請項目的列表沿用 SMS 的 /api/sms/scholarships?only_open=true。）
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.sas import service
from app.modules.sas.schemas import ApplicationCreate, ApplicationOut

router = APIRouter(prefix="/api/sas", tags=["SAS 學生申請"])


@router.post(
    "/applications",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
def apply(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    """學生線上申請獎學金（NUKSAMS012）。"""
    return service.apply(db, student, body)


@router.get("/applications/me", response_model=list[ApplicationOut])
def my_applications(
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    """查詢自己所有申請案的進度（NUKSAMS014）。"""
    return service.list_my_applications(db, student)
