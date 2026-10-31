from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "Viewer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class EventCreate(BaseModel):
    source: str = Field(default="unknown", min_length=1, max_length=120)
    event_type: str = Field(default="generic", min_length=1, max_length=120)
    severity: str = Field(default="info", pattern="^(info|low|medium|high|critical)$")
    host: Optional[str] = Field(default=None, max_length=120)
    user: Optional[str] = Field(default=None, max_length=120)
    src_ip: Optional[str] = Field(default=None, max_length=120)
    dst_ip: Optional[str] = Field(default=None, max_length=120)
    process_name: Optional[str] = Field(default=None, max_length=200)
    message: str = Field(min_length=1, max_length=10000)
    raw: Optional[str] = Field(default=None, max_length=100000)
    timestamp: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @field_validator("metadata")
    @classmethod
    def normalize_metadata(cls, value: dict[str, Any] | None) -> dict[str, Any]:
        return value or {}


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    id: int
    source: str = "unknown"
    event_type: str = "generic"
    severity: str = "info"
    host: Optional[str] = None
    user: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    process_name: Optional[str] = None
    message: str
    raw: Optional[str] = None
    timestamp: datetime
    payload_metadata: dict[str, Any] = Field(
        default_factory=dict,
        serialization_alias="metadata",
    )


T = TypeVar("T")


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    pagination: dict[str, int]


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    severity: str
    status: str
    source: str
    summary: Optional[str] = None
    event_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    alert_metadata: dict[str, Any] = Field(default_factory=dict, serialization_alias="metadata")


class DetectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    severity: str
    rule_id: Optional[str] = None
    description: Optional[str] = None
    mitre: List[dict[str, Any]] = Field(default_factory=list)
    enabled: bool
    created_at: datetime


class CaseCreate(BaseModel):
    title: str
    priority: str = "medium"
    assigned_to: Optional[str] = None
    summary: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)


class CaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    summary: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    created_at: datetime


class ReportCreate(BaseModel):
    title: str
    report_type: str = "investigation"
    format: str = "markdown"


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    report_type: str
    format: str
    content: str
    created_at: datetime
