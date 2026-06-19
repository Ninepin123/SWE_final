"""SAS 學生申請 — API 路由
需求書：Chapter 6。範圍：線上申請（含申請表）、查詢自己的申請進度、維護個人資料。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas.models import User
from app.modules.aas.security import require_roles
from app.modules.sas import service
from app.modules.sas.schemas import (
    ApplicationCreate,
    ApplicationDocumentOut,
    ApplicationDocumentWrite,
    ApplicationOut,
    ApplicationUpdate,
    ProfileOut,
    ProfileUpdate,
    ScholarshipEligibilityOut,
    SupplementRequestCreate,
    SupplementRequestOut,
    SupplementSubmit,
)

router = APIRouter(prefix="/api/sas", tags=["SAS 學生申請"])


@router.get("/scholarships/available", response_model=list[ScholarshipEligibilityOut])
def available_scholarships(
    keyword: str | None = None,
    category: str | None = None,
    department: str | None = None,
    deadline_before: datetime | None = None,
    eligible_only: bool = False,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.list_scholarships_for_student(
        db,
        student,
        keyword=keyword,
        category=category,
        department=department,
        deadline_before=deadline_before,
        eligible_only=eligible_only,
    )


@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def create_draft(
    body: ApplicationCreate,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.create_draft(db, student, body)


@router.get("/applications/me", response_model=list[ApplicationOut])
def my_applications(db: Session = Depends(get_db), student: User = Depends(require_roles("STUDENT"))):
    return service.list_my_applications(db, student)


@router.get("/applications/{application_id}", response_model=ApplicationOut)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.get_my_application(db, student, application_id)


@router.put("/applications/{application_id}", response_model=ApplicationOut)
def update_draft(
    application_id: int,
    body: ApplicationUpdate,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.update_draft(db, student, application_id, body)


@router.post("/applications/{application_id}/submit", response_model=ApplicationOut)
def submit_application(
    application_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.submit_application(db, student, application_id)


@router.get(
    "/applications/{application_id}/documents",
    response_model=list[ApplicationDocumentOut],
)
def list_documents(
    application_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.list_documents(db, student, application_id)


@router.post(
    "/applications/{application_id}/documents",
    response_model=ApplicationDocumentOut,
)
def save_document(
    application_id: int,
    body: ApplicationDocumentWrite,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.save_text_document(db, student, application_id, body)


@router.delete("/applications/{application_id}/documents/{document_id}")
def delete_document(
    application_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    service.delete_document(db, student, application_id, document_id)
    return {"detail": "已刪除文字文件"}


@router.post(
    "/applications/{application_id}/supplement-requests",
    response_model=SupplementRequestOut,
)
def create_supplement_request(
    application_id: int,
    body: SupplementRequestCreate,
    db: Session = Depends(get_db),
    reviewer: User = Depends(require_roles("REVIEWER")),
):
    return service.create_supplement_request(db, reviewer, application_id, body)


@router.get(
    "/applications/{application_id}/supplement-requests",
    response_model=list[SupplementRequestOut],
)
def list_supplement_requests(
    application_id: int,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.list_supplement_requests(db, student, application_id)


@router.post(
    "/applications/{application_id}/supplement-requests/{supplement_id}/submit",
    response_model=SupplementRequestOut,
)
def submit_supplement(
    application_id: int,
    supplement_id: int,
    body: SupplementSubmit,
    db: Session = Depends(get_db),
    student: User = Depends(require_roles("STUDENT")),
):
    return service.submit_supplement(
        db, student, application_id, supplement_id, body
    )


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
