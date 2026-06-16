"""SMS 獎助學金資料管理 — API 路由
需求書：Chapter 5，功能需求 5.2.1–5.2.5
v1 範圍：獎學金的列表/查詢（所有登入者），以及單位/管理員的新增。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import get_current_user, require_roles
from app.modules.sms import service
from app.modules.sms.schemas import ScholarshipCreate, ScholarshipOut

router = APIRouter(prefix="/api/sms", tags=["SMS 獎助學金資料管理"])


@router.get("/scholarships", response_model=list[ScholarshipOut])
def list_scholarships(
    only_open: bool = False,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """查詢獎學金；only_open=true 只回傳尚未截止且開放中的項目（NUKSAMS013）。"""
    return service.list_scholarships(db, only_open=only_open)


@router.get("/scholarships/{scholarship_id}", response_model=ScholarshipOut)
def get_scholarship(
    scholarship_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return service.get_scholarship(db, scholarship_id)


@router.post(
    "/scholarships",
    response_model=ScholarshipOut,
    status_code=status.HTTP_201_CREATED,
)
def create_scholarship(
    body: ScholarshipCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_roles("SPONSOR", "ADMIN")),
):
    """新增獎學金（NUKSAMS005，僅獎助單位/管理員）。"""
    return service.create_scholarship(db, body, current)
