"""Create the required bootstrap administrator account.

This is system bootstrap data, not demo/mock content. It only creates one
administrator when the database has no ADMIN account yet.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.modules.aas.models import AuditLog, User
from app.modules.aas.security import hash_password


def ensure_bootstrap_admin(db: Session) -> tuple[User, bool]:
    existing_admin = db.scalar(
        select(User).where(User.role == "ADMIN").order_by(User.user_id.asc())
    )
    if existing_admin is not None:
        return existing_admin, False

    account = settings.bootstrap_admin_account.strip()
    password = settings.bootstrap_admin_password
    name = settings.bootstrap_admin_name.strip() or "系統管理員"
    email = settings.bootstrap_admin_email.strip() if settings.bootstrap_admin_email else None

    if not account:
        raise RuntimeError("BOOTSTRAP_ADMIN_ACCOUNT 不可為空")
    if not password or len(password) < 8:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD 至少需要 8 個字元")

    account_owner = db.scalar(select(User).where(User.account == account))
    if account_owner is not None:
        raise RuntimeError(
            f"帳號 {account} 已存在但不是 ADMIN，無法建立預設管理員。"
        )

    admin = User(
        account=account,
        password=hash_password(password),
        name=name,
        email=email,
        role="ADMIN",
        status="ACTIVE",
    )
    db.add(admin)
    db.flush()
    db.add(
        AuditLog(
            actor_id=admin.user_id,
            action="BOOTSTRAP_ADMIN_CREATED",
            target_type="user",
            target_id=admin.user_id,
            detail=f"建立預設管理員帳號 {account}",
        )
    )
    db.commit()
    db.refresh(admin)
    return admin, True


def main() -> None:
    db = SessionLocal()
    try:
        admin, created = ensure_bootstrap_admin(db)
    finally:
        db.close()

    if created:
        print(f"  v 已建立預設管理員帳號：{admin.account}")
        print("    密碼來自 BOOTSTRAP_ADMIN_PASSWORD，首次登入後請立即修改。")
    else:
        print(f"  v 已存在管理員帳號：{admin.account}，略過建立。")


if __name__ == "__main__":
    main()
