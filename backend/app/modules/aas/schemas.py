"""AAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    account: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    account: str
    name: str
    role: str
    email: str | None = None
    unit_id: int | None = None
    department: str | None = None
    gpa: float | None = None
    status: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class UserCreate(BaseModel):
    account: str
    password: str
    name: str
    role: str
    email: str | None = None
    unit_id: int | None = None
    department: str | None = None
    gpa: float | None = None


class UserUpdate(BaseModel):
    # 只更新有送來的欄位（exclude_unset）。password 留空表示不改。
    name: str | None = None
    email: str | None = None
    role: str | None = None
    unit_id: int | None = None
    department: str | None = None
    gpa: float | None = None
    status: str | None = None
    password: str | None = None


class TeacherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    name: str
    department: str | None = None


class AuditLogOut(BaseModel):
    log_id: int
    actor_id: int | None = None
    actor_name: str | None = None
    action: str
    target_type: str | None = None
    target_id: int | None = None
    detail: str | None = None
    created_at: datetime
