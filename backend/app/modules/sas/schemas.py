"""SAS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    scholarship_id: int
    statement: str | None = None


class ApplicationOut(BaseModel):
    application_id: int
    scholarship_id: int
    scholarship_name: str | None = None
    status: str
    statement: str | None = None
    created_at: datetime
