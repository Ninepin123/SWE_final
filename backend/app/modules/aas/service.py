"""AAS — 商業邏輯層（登入驗證、帳號 CRUD）。"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.aas.models import User
from app.modules.aas.schemas import UserCreate
from app.modules.aas.security import hash_password, verify_password

VALID_ROLES = {"STUDENT", "TEACHER", "SPONSOR", "REVIEWER", "ADMIN"}


def authenticate(db: Session, account: str, password: str) -> User:
    user = db.scalar(select(User).where(User.account == account))
    if user is None or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="帳號已停用")
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.user_id)))


def create_user(db: Session, data: UserCreate) -> User:
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="角色不存在")
    if db.scalar(select(User).where(User.account == data.account)):
        raise HTTPException(status_code=409, detail="帳號已存在")
    user = User(
        account=data.account,
        password=hash_password(data.password),
        name=data.name,
        email=data.email,
        role=data.role,
        unit_id=data.unit_id,
        department=data.department,
        gpa=data.gpa,
        status="ACTIVE",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
