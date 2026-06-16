"""SMS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel


class ScholarshipCreate(BaseModel):
    name: str
    year: int
    amount: int = 0
    quota: int = 1
    min_gpa: float | None = None
    department_limit: str | None = None
    category: str = "OTHER"  # SCHOOL/GOVERNMENT/PRIVATE/LOW_INCOME/MERIT/OTHER
    description: str | None = None
    deadline: datetime | None = None


class ScholarshipOut(BaseModel):
    scholarship_id: int
    name: str
    year: int
    amount: int
    quota: int
    min_gpa: float | None = None
    department_limit: str | None = None
    category: str
    description: str | None = None
    deadline: datetime | None = None
    status: str
    unit_id: int
    unit_name: str | None = None
