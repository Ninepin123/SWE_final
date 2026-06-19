"""AAS — 商業邏輯層（登入驗證、帳號 CRUD、稽核紀錄）。"""
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.aas.models import AuditLog, User
from app.modules.aas.schemas import UserCreate, UserUpdate
from app.modules.aas.security import hash_password, verify_password

VALID_ROLES = {"STUDENT", "TEACHER", "SPONSOR", "REVIEWER", "ADMIN"}
VALID_STATUS = {"ACTIVE", "DISABLED"}


def authenticate(db: Session, account: str, password: str) -> User:
    user = db.scalar(select(User).where(User.account == account))
    if user is None or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="帳號已停用")
    return user


def list_users(
    db: Session,
    keyword: str | None = None,
    role: str | None = None,
    unit_id: int | None = None,
    account_status: str | None = None,
) -> list[User]:
    stmt = select(User)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                User.account.ilike(pattern),
                User.name.ilike(pattern),
                User.email.ilike(pattern),
                User.department.ilike(pattern),
            )
        )
    if role:
        if role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="角色不存在")
        stmt = stmt.where(User.role == role)
    if unit_id is not None:
        stmt = stmt.where(User.unit_id == unit_id)
    if account_status:
        if account_status not in VALID_STATUS:
            raise HTTPException(status_code=400, detail="狀態不存在")
        stmt = stmt.where(User.status == account_status)
    return list(db.scalars(stmt.order_by(User.user_id)))


def list_teachers(db: Session) -> list[User]:
    return list(db.scalars(select(User).where(User.role == "TEACHER").order_by(User.name)))


def create_user(db: Session, data: UserCreate) -> User:
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="角色不存在")
    if db.scalar(select(User).where(User.account == data.account)):
        raise HTTPException(status_code=409, detail="帳號已存在")
    if not data.password.strip():
        raise HTTPException(status_code=400, detail="密碼不可為空")
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


def update_user(db: Session, user_id: int, data: UserUpdate, current_user_id: int | None = None) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="找不到帳號")
    payload = data.model_dump(exclude_unset=True)
    if "role" in payload and payload["role"] not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="角色不存在")
    if "status" in payload and payload["status"] not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="狀態不存在")
    if current_user_id == user_id and payload.get("status") == "DISABLED":
        raise HTTPException(status_code=400, detail="不能停用目前登入的管理員帳號")
    if "password" in payload:
        pw = payload.pop("password")
        if pw:
            user.password = hash_password(pw)
    for key, value in payload.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, current_user_id: int | None = None) -> None:
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="不能刪除目前登入的管理員帳號")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="找不到帳號")
    try:
        db.delete(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="此帳號已有關聯資料（申請/審查/推薦等），無法刪除；建議改為「停用」。")


def write_audit(db: Session, actor_id: int | None, action: str, target_type: str | None = None,
                target_id: int | None = None, detail: str | None = None, commit: bool = True) -> AuditLog:
    log = AuditLog(actor_id=actor_id, action=action, target_type=target_type, target_id=target_id, detail=detail)
    db.add(log)
    if commit:
        db.commit()
    return log


def list_audit_logs(db: Session, limit: int = 200) -> list[dict]:
    rows = db.execute(
        select(AuditLog, User.name)
        .join(User, AuditLog.actor_id == User.user_id, isouter=True)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "log_id": log.log_id,
            "actor_id": log.actor_id,
            "actor_name": name,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "created_at": log.created_at,
        }
        for log, name in rows
    ]
