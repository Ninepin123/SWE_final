"""AAS — 認證與授權共用工具（密碼雜湊、JWT、登入者 dependency）。

依需求書 4.2.1（登入）與 4.2.3（角色權限）。
其他子系統一律從這裡 import get_current_user / require_roles，
不要自己解析 token 或讀 user 資料表。
"""
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.aas.models import User

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=True)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str, jti: str | None = None) -> str:
    """簽發 JWT。jti（session 識別碼）用於 AAS003 單一登入；省略時為一般無狀態 token。"""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    if jti is not None:
        payload["jti"] = jti
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """解析 Bearer JWT，回傳目前登入的 User（其他子系統共用）。"""
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登入憑證無效或已過期",
        headers={"WWW-Authenticate": "Bearer"},
    )
    session_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="帳號已在其他裝置登入，此連線已失效",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise cred_exc
    user = db.get(User, user_id)
    if user is None or user.status != "ACTIVE":
        raise cred_exc
    # AAS003 單一登入：登入流程簽發的 token 帶 jti，必須與帳號目前的 session_token 相符。
    # 重新登入（輪替）或登出（清空）都會使先前的 token 失效。
    token_jti = payload.get("jti")
    if user.session_token is not None:
        if token_jti != user.session_token:
            raise session_exc
    elif token_jti is not None:
        # 帳號已登出（session 已清空），但 token 仍帶 jti → 視為失效
        raise session_exc
    return user


def require_roles(*roles: str):
    """產生一個 dependency，限定只有指定角色可存取。

    用法：_: User = Depends(require_roles("ADMIN"))
    """
    def checker(current: User = Depends(get_current_user)) -> User:
        if roles and current.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="權限不足")
        return current

    return checker
