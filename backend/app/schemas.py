from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


class EventCreate(BaseModel):
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
    timestamp: Optional[datetime] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventOut(EventCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime


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
    metadata: dict[str, Any] = Field(default_factory=dict)


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
