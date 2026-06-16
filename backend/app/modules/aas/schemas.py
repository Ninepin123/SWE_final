"""AAS — Pydantic schema（API 的 request / response 格式）。

介面契約同步在 docs/API.md。
"""
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
