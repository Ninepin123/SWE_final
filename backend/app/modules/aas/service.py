"""AAS — 商業邏輯層（登入驗證、帳號 CRUD、稽核紀錄、單一登入 session）。"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.modules.aas.models import AuditLog, Unit, User
from app.modules.aas.schemas import UnitCreate, UnitUpdate, UserCreate, UserUpdate
from app.modules.aas.security import hash_password, verify_password

VALID_ROLES = {"STUDENT", "TEACHER", "SPONSOR", "REVIEWER", "ADMIN"}
VALID_STATUS = {"ACTIVE", "DISABLED"}
VALID_UNIT_TYPES = {"SCHOOL", "GOVERNMENT", "PRIVATE", "OTHER"}


def _utcnow() -> datetime:
    """以 naive UTC 儲存/比較 session 到期時間，避免 tz-aware 與資料庫欄位混用。"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _audit_datetime(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def authenticate(db: Session, account: str, password: str) -> User:
    user = db.scalar(select(User).where(User.account == account))
    if user is None or not verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="帳號已停用")
    return user


def get_active_user_by_role(db: Session, role: str) -> User:
    user = db.scalar(
        select(User)
        .where(User.role == role, User.status == "ACTIVE")
        .order_by(User.user_id.asc())
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"找不到可用的 {role} 測試帳號")
    return user


def start_session(db: Session, user: User) -> str:
    """AAS003：登入時建立新的 session 識別碼並輪替舊值（使其他裝置的 token 失效）。"""
    jti = uuid.uuid4().hex
    user.session_token = jti
    user.session_expires_at = _utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    db.commit()
    return jti


def end_session(db: Session, user: User) -> None:
    """登出：清空 session，使現有 token 立即失效。"""
    user.session_token = None
    user.session_expires_at = None
    db.commit()


def count_online_users(db: Session) -> int:
    """AAS015：線上人數 = 仍有有效 session（未過期）的帳號數。"""
    return int(
        db.scalar(
            select(func.count(User.user_id)).where(
                User.session_token.is_not(None),
                User.session_expires_at.is_not(None),
                User.session_expires_at > _utcnow(),
            )
        )
        or 0
    )


def write_login_audit(db: Session, account: str, success: bool, detail: str) -> AuditLog:
    user = db.scalar(select(User).where(User.account == account))
    return write_audit(
        db,
        user.user_id if user else None,
        "LOGIN_SUCCESS" if success else "LOGIN_FAILED",
        "user",
        user.user_id if user else None,
        f"帳號 {account}：{detail}",
    )


# --- 單位管理（4.2 單位資料；獎助/審查單位以此做資料隔離） ---


def list_units(db: Session, keyword: str | None = None) -> list[Unit]:
    stmt = select(Unit)
    if keyword and keyword.strip():
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Unit.name.ilike(pattern), Unit.contact_email.ilike(pattern)))
    return list(db.scalars(stmt.order_by(Unit.unit_id)))


def create_unit(db: Session, data: UnitCreate) -> Unit:
    if data.type not in VALID_UNIT_TYPES:
        raise HTTPException(status_code=400, detail="單位類型不存在")
    name = data.name.strip()
    if db.scalar(select(Unit).where(Unit.name == name)):
        raise HTTPException(status_code=409, detail="單位名稱已存在")
    unit = Unit(name=name, type=data.type, contact_email=data.contact_email)
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


def update_unit(db: Session, unit_id: int, data: UnitUpdate) -> Unit:
    unit = db.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="找不到單位")
    payload = data.model_dump(exclude_unset=True)
    if "type" in payload and payload["type"] not in VALID_UNIT_TYPES:
        raise HTTPException(status_code=400, detail="單位類型不存在")
    if "name" in payload and payload["name"] is not None:
        payload["name"] = payload["name"].strip()
        if db.scalar(select(Unit).where(Unit.name == payload["name"], Unit.unit_id != unit_id)):
            raise HTTPException(status_code=409, detail="單位名稱已存在")
    for key, value in payload.items():
        setattr(unit, key, value)
    db.commit()
    db.refresh(unit)
    return unit


def delete_unit(db: Session, unit_id: int) -> None:
    unit = db.get(Unit, unit_id)
    if unit is None:
        raise HTTPException(status_code=404, detail="找不到單位")
    bound_users = db.scalar(select(func.count(User.user_id)).where(User.unit_id == unit_id)) or 0
    if bound_users:
        raise HTTPException(status_code=409, detail="仍有帳號綁定此單位，請先改綁其他單位再刪除。")
    # 獎學金以 unit_id 外鍵相依；延後匯入避免與 SMS 模組循環引用。
    from app.modules.sms.models import Scholarship

    bound_scholarships = db.scalar(
        select(func.count(Scholarship.scholarship_id)).where(Scholarship.unit_id == unit_id)
    ) or 0
    if bound_scholarships:
        raise HTTPException(status_code=409, detail="此單位仍有獎學金，請先轉移或刪除獎學金再刪除單位。")
    try:
        db.delete(unit)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="此單位已被其他資料引用，無法刪除。")


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


def list_audit_logs(
    db: Session,
    actor_id: int | str | None = None,
    action: str | None = None,
    target_type: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 200,
) -> list[dict]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="查詢筆數需介於 1 到 500")
    actor_filter = str(actor_id).strip() if actor_id is not None else ""
    created_from = _audit_datetime(created_from)
    created_to = _audit_datetime(created_to)
    stmt = select(AuditLog, User.name).join(
        User, AuditLog.actor_id == User.user_id, isouter=True
    )
    if actor_filter:
        if actor_filter.isdecimal():
            stmt = stmt.where(AuditLog.actor_id == int(actor_filter))
        else:
            account_candidates = {actor_filter}
            if actor_filter.startswith("u-") and len(actor_filter) > 2:
                account_candidates.add(actor_filter[2:])
            stmt = stmt.where(or_(User.account.in_(account_candidates), User.name.ilike(f"%{actor_filter}%")))
    if action and action.strip():
        stmt = stmt.where(AuditLog.action == action.strip())
    if target_type and target_type.strip():
        stmt = stmt.where(AuditLog.target_type == target_type.strip())
    if created_from is not None:
        stmt = stmt.where(AuditLog.created_at >= created_from)
    if created_to is not None:
        stmt = stmt.where(AuditLog.created_at <= created_to)
    rows = db.execute(stmt.order_by(AuditLog.created_at.desc(), AuditLog.log_id.desc()).limit(limit)).all()
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
