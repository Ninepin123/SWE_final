"""AAS 帳號與權限管理 — API 路由
需求書：Chapter 4，功能需求 4.2.1–4.2.6
範圍：登入/登出/查目前登入者；管理員的帳號 CRUD（新增/查詢/修改/刪除）；
      老師清單（給學生邀請推薦用）；稽核紀錄查詢。
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.aas import service
from app.modules.aas.models import User
from app.modules.aas.monitoring import build_metrics, metrics
from app.modules.trs import service as trs_service
from app.modules.aas.schemas import (
    AuditLogOut,
    LoginRequest,
    MonitoringMetricsOut,
    RoleQuickLoginRequest,
    TeacherOut,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.modules.aas.security import create_access_token, get_current_user, require_roles

router = APIRouter(prefix="/api/aas", tags=["AAS 帳號與權限管理"])
VALID_ROLES = {"STUDENT", "TEACHER", "SPONSOR", "REVIEWER", "ADMIN"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = service.authenticate(db, body.account, body.password)
    except HTTPException as exc:
        service.write_login_audit(db, body.account, success=False, detail=exc.detail)
        metrics.record_login_failure()  # AAS016：累計登入失敗供異常警示
        raise
    service.write_audit(db, user.user_id, "LOGIN_SUCCESS", "user", user.user_id, "登入成功")
    # AAS003：建立單一登入 session，將 jti 寫入 token；其他裝置先前的 token 立即失效。
    jti = service.start_session(db, user)
    token = create_access_token(user.user_id, user.role, jti=jti)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/dev-login-as", response_model=TokenResponse)
def dev_login_as(body: RoleQuickLoginRequest, db: Session = Depends(get_db)):
    """開發用快速登入：依角色直接取得一個啟用中的帳號。"""
    if not settings.enable_dev_quick_login:
        raise HTTPException(status_code=404, detail="Not Found")

    role = body.role.strip().upper()
    if role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="角色不存在")

    user = service.get_active_user_by_role(db, role)
    if role == "TEACHER":
        trs_service.ensure_dev_teacher_recommendations(db, user, count=6)
    service.write_audit(db, user.user_id, "DEV_QUICK_LOGIN", "user", user.user_id, f"開發快速登入（{role}）")
    jti = service.start_session(db, user)
    token = create_access_token(user.user_id, user.role, jti=jti)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    service.end_session(db, current)
    service.write_audit(db, current.user_id, "LOGOUT", "user", current.user_id, "登出成功")
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
def audit_logs(
    actor_id: int | None = None,
    action: str | None = None,
    target_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    """稽核紀錄（4.2.5，僅管理員）。"""
    return service.list_audit_logs(
        db,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        created_from=created_from,
        created_to=created_to,
        limit=limit,
    )


@router.get("/monitoring/metrics", response_model=MonitoringMetricsOut)
def monitoring_metrics(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    """系統維運監控（AAS015-016，僅管理員）：線上人數、負載、錯誤率與異常警示。"""
    return build_metrics(db)
