from datetime import datetime, timezone
from typing import Any, Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PasswordPolicy(BaseModel):
    password: str = Field(min_length=12, max_length=128)


class UserCreate(PasswordPolicy):
    username: str = Field(min_length=3, max_length=80, pattern="^[A-Za-z0-9_.-]+$")
    email: EmailStr
    role: str = Field(default="SECURITY_VIEWER", exclude=True)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: str
    disabled: int = 0
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=4096)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(PasswordPolicy):
    token: str = Field(min_length=20, max_length=4096)


class EventCreate(BaseModel):
    external_id: Optional[str] = Field(default=None, max_length=255)
    idempotency_key: Optional[str] = Field(default=None, max_length=255)
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


class EventBatchCreate(BaseModel):
    events: List[EventCreate] = Field(min_length=1, max_length=500)


class EventIngestResult(BaseModel):
    accepted: bool
    duplicate: bool = False
    id: Optional[int] = None
    index: Optional[int] = None
    errors: Optional[list[str]] = None


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


class EvidenceReference(BaseModel):
    reference_type: Literal["event", "alert", "rule", "case", "intel", "mitre"]
    reference_id: str
    label: str


class InvestigationFinding(BaseModel):
    title: str
    description: str
    evidence_references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    observed_fact: bool = False


class AttackAnalysis(BaseModel):
    potential_technique: str
    tactic: str | None = None
    technique_id: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    potential_impact: str
    severity_assessment: str
    confidence: float = Field(ge=0, le=1)
    uncertainty: str
    missing_evidence: list[str] = Field(default_factory=list)


class InvestigationResultSchema(BaseModel):
    executive_summary: str
    alert_severity: str
    detection_rule: str | None = None
    event_count: int = Field(ge=0)
    affected_assets: list[str] = Field(default_factory=list)
    affected_users: list[str] = Field(default_factory=list)
    investigation_status: str = "requires_review"
    findings: list[InvestigationFinding] = Field(default_factory=list)
    attack_analysis: list[AttackAnalysis] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    recommended_investigation_steps: list[str] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    actions_already_performed: list[str] = Field(default_factory=list)
    actions_requiring_approval: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    alert_id: int
    case_id: int | None = None
    status: str
    provider: str
    model: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    error_category: str | None = None
    version: int
    result: InvestigationResultSchema | None = None
    evidence_references: list[str] = Field(default_factory=list)
    fallback: bool = False


class InvestigationCreate(BaseModel):
    alert_id: int | None = Field(default=None, gt=0)
    case_id: int | None = Field(default=None, gt=0)
    force_rerun: bool = False


class InvestigationFeedbackCreate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    comments: str | None = Field(default=None, max_length=2000)
