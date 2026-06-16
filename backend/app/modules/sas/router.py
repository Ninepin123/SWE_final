"""SAS 學生申請 — API 路由
需求書：Chapter 6。範圍：線上申請（含申請表）、查詢自己的申請進度、維護個人資料。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.sas import service
from app.modules.sas.schemas import ApplicationCreate, ApplicationOut, ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/sas", tags=["SAS 學生申請"])


@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply(body: ApplicationCreate, db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))):
    return service.apply(db, student, body)


@router.get("/applications/me", response_model=list[ApplicationOut])
def my_applications(db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))):
    return service.list_my_applications(db, student)


@router.get("/profile", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))):
    """查詢自己的個人資料（學號等核心欄位唯讀）。"""
    return service.get_profile(db, student)


@router.put("/profile", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate, db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))
):
    """更新自己的可編輯個人資料（6.2.1：學號/姓名/GPA 等不可由學生修改）。"""
    return service.update_profile(db, student, body)
