"""AAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    account: str
    password: str


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    unit_id: int
    name: str
    type: str
    contact_email: str | None = None
    created_at: datetime | None = None


class UnitCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = "OTHER"
    contact_email: str | None = None


class UnitUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: str | None = None
    contact_email: str | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    department_id: int
    name: str
    college: str | None = None
    category: str
    created_at: datetime | None = None


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    college: str | None = None
    category: str = "ACADEMIC"


class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    college: str | None = None
    category: str | None = None


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
    account: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
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
    password: str | None = Field(default=None, min_length=8, max_length=128)


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


# AAS015-016 系統維運監控
class ServerLoadOut(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float


class MonitoringAlertOut(BaseModel):
    level: str          # CRITICAL / WARNING
    code: str
    message: str


class MonitoringMetricsOut(BaseModel):
    online_users: int
    total_users: int
    uptime_seconds: float
    requests_total: int
    errors_total: int
    error_rate: float
    login_failures_total: int
    server_load: ServerLoadOut | None = None
    alerts: list[MonitoringAlertOut] = []
