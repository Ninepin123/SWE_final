"""SMS — Pydantic schema。介面契約同步在 docs/API.md。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CriteriaSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    min_gpa: float | None = None
    departments: list[str] | None = None
    grades: list[str] | None = None
    identities: list[str] | None = None
    family_statuses: list[str] | None = None
    note: str | None = None


class ScholarshipCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    name: str = Field(alias="title")
    year: int = Field(default_factory=lambda: datetime.now().year)
    amount: int = 0
    quota: int = 1
    used_quota: int = 0
    category: str = "OTHER"
    description: str | None = None
    start_date: datetime | None = None
    deadline: datetime | None = None
    status: str = "OPEN"
    criteria: CriteriaSchema | None = None
    tags: list[str] | None = None
    required_docs: list[str] | None = None
    require_recommendation: bool = False
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_address: str | None = None
    website: str | None = None

class ScholarshipUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    name: str | None = Field(None, alias="title")
    year: int | None = None
    amount: int | None = None
    quota: int | None = None
    used_quota: int | None = None
    category: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    deadline: datetime | None = None
    status: str | None = None  # OPEN / CLOSED
    criteria: CriteriaSchema | None = None
    tags: list[str] | None = None
    required_docs: list[str] | None = None
    require_recommendation: bool | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_address: str | None = None
    website: str | None = None

class ScholarshipOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: int = Field(alias="scholarshipId", validation_alias="scholarship_id")
    title: str = Field(validation_alias="name")
    year: int
    amount: int
    quota: int
    used_quota: int = Field(0, validation_alias="used_quota")
    category: str
    description: str | None = None
    start_date: datetime | None = None
    deadline: datetime | None = None
    status: str
    unit_id: int
    sponsor: str | None = Field(None, validation_alias="unit_name")
    criteria: CriteriaSchema | None = None
    tags: list[str] | None = None
    required_docs: list[str] | None = None
    require_recommendation: bool = False
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    contact_address: str | None = None
    website: str | None = None
    is_open: bool = False

class OptionCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    type: str  # CATEGORY, TAG
    name: str


class OptionOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    option_id: int = Field(alias="id")
    type: str
    name: str
