"""AAS 帳號與權限管理 — API 路由
需求書：Chapter 4，功能需求 4.2.1–4.2.6
v1 範圍：登入/登出/查目前登入者，以及管理員的帳號查詢/新增。
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.aas import service
from app.modules.aas.models import User
from app.modules.aas.schemas import LoginRequest, TokenResponse, UserCreate, UserOut
from app.modules.aas.security import create_access_token, get_current_user, require_roles

router = APIRouter(prefix="/api/aas", tags=["AAS 帳號與權限管理"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """使用者登入（UC001），驗證帳密後回傳 JWT 與使用者資訊。"""
    user = service.authenticate(db, body.account, body.password)
    token = create_access_token(user.user_id, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/logout")
def logout(current: User = Depends(get_current_user)):
    """登出（UC002）。JWT 為無狀態，實際清除由前端移除 token 完成。"""
    return {"detail": "已登出"}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    """回傳目前登入者資訊。"""
    return current


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_roles("ADMIN"))):
    """查詢所有帳號（UC004，僅管理員）。"""
    return service.list_users(db)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("ADMIN")),
):
    """新增帳號（UC003，僅管理員）。"""
    return service.create_user(db, body)
