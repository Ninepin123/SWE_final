"""AAS 帳號與權限管理 — API 路由
需求書：Chapter 4，功能需求 4.2.1–4.2.6
範圍：登入/登出/查目前登入者；管理員的帳號 CRUD（新增/查詢/修改/刪除）；
      老師清單（給學生邀請推薦用）；稽核紀錄查詢。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas import service
from app.modules.aas.models import User
from app.modules.aas.schemas import (
    AuditLogOut,
    LoginRequest,
    TeacherOut,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.modules.aas.security import create_access_token, get_current_user, require_roles

router = APIRouter(prefix="/api/aas", tags=["AAS 帳號與權限管理"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = service.authenticate(db, body.account, body.password)
    token = create_access_token(user.user_id, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current: User = Depends(get_current_user)):
    return {"detail": "已登出"}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.get("/teachers", response_model=list[TeacherOut])
def list_teachers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """老師清單（給學生在邀請推薦時挑選）。"""
    return service.list_teachers(db)


@router.get("/users", response_model=list[UserOut])
def list_users(
    keyword: str | None = None,
    role: str | None = None,
    unit_id: int | None = None,
    account_status: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    return service.list_users(
        db,
        keyword=keyword,
        role=role,
        unit_id=unit_id,
        account_status=account_status,
    )


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))):
    user = service.create_user(db, body)
    service.write_audit(db, current.user_id, "CREATE_USER", "user", user.user_id, f"新增帳號 {user.account}（{user.role}）")
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int, body: UserUpdate, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))
):
    user = service.update_user(db, user_id, body, current_user_id=current.user_id)
    service.write_audit(db, current.user_id, "UPDATE_USER", "user", user_id, f"修改帳號 {user.account}")
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current: User = Depends(require_roles("ADMIN"))):
    service.delete_user(db, user_id, current_user_id=current.user_id)
    service.write_audit(db, current.user_id, "DELETE_USER", "user", user_id, f"刪除帳號 #{user_id}")
    return {"detail": "已刪除帳號"}


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    """稽核紀錄（4.2.5，僅管理員）。"""
    return service.list_audit_logs(db)
