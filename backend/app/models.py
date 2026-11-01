from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="SECURITY_VIEWER")
    disabled = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(120), default="unknown")
    event_type = Column(String(120), default="generic")
    severity = Column(String(50), default="info")
    host = Column(String(120), nullable=True)
    user = Column(String(120), nullable=True)
    src_ip = Column(String(120), nullable=True)
    dst_ip = Column(String(120), nullable=True)
    process_name = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    raw = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    payload_metadata = Column(JSON, default=dict)
    external_id = Column(String(255), nullable=True, unique=True, index=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    ingestion_status = Column(String(50), default="accepted", nullable=False)
    processing_status = Column(String(50), default="pending", nullable=False)
    processed_at = Column(DateTime, nullable=True)
    processing_attempts = Column(Integer, default=0, nullable=False)
    last_processing_error = Column(Text, nullable=True)


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    status = Column(String(50), default="pending", nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    next_attempt_at = Column(DateTime, nullable=True, index=True)
    claimed_at = Column(DateTime, nullable=True)
    claimed_by = Column(String(255), nullable=True)
    terminal_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint("notification_id", name="uq_notifications_notification_id"),
        {"extend_existing": True},
    )
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String(255), unique=True, nullable=False, index=True)
    event_type = Column(String(120), nullable=False, index=True)
    schema_version = Column(Integer, default=1, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    resource_type = Column(String(80), nullable=False)
    resource_id = Column(String(255), nullable=False, index=True)
    data = Column(JSON, default=dict)


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), default="medium")
    status = Column(String(50), default="open")
    source = Column(String(120), default="detection")
    summary = Column(Text, nullable=True)
    event_ids = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    alert_metadata = Column(JSON, default=dict)
    fingerprint = Column(String(255), nullable=True, index=True)
    first_observed_at = Column(DateTime, nullable=True)
    last_observed_at = Column(DateTime, nullable=True)


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    severity = Column(String(50), default="medium")
    rule_id = Column(String(120), nullable=True)
    description = Column(Text, nullable=True)
    mitre = Column(JSON, default=list)
    enabled = Column(Integer, default=1)
    fingerprint = Column(String(255), unique=True, nullable=True, index=True)
    event_ids = Column(JSON, default=list)
    first_observed_at = Column(DateTime, nullable=True)
    last_observed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    rule_id = Column(String(120), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=True)
    version = Column(Integer, default=1, nullable=False)
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class RuleVersion(Base):
    __tablename__ = "rule_versions"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(
        String(120), ForeignKey("rules.rule_id", ondelete="CASCADE"), nullable=False, index=True
    )
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    status = Column(String(50), default="open")
    priority = Column(String(50), default="medium")
    assigned_to = Column(String(120), nullable=True)
    summary = Column(Text, nullable=True)
    evidence = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = relationship("CaseNote", back_populates="case", cascade="all, delete-orphan")


class CaseNote(Base):
    __tablename__ = "case_notes"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    author = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    case = relationship("Case", back_populates="notes")


class ThreatIntel(Base):
    __tablename__ = "threat_intel"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(String(255), nullable=False, index=True)
    normalized_value = Column(String(255), nullable=False, unique=True, index=True)
    intel_type = Column(String(80), default="ip")
    severity = Column(String(80), default="medium")
    details = Column(Text, nullable=True)
    confidence = Column(Integer, default=0, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    source = Column(String(120), default="manual")
    original_value = Column(String(255), nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    active = Column(Integer, default=1, nullable=False, index=True)
    external_reference = Column(String(500), nullable=True)
    provenance = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class IOCMatch(Base):
    __tablename__ = "ioc_matches"
    __table_args__ = (
        UniqueConstraint("event_id", "indicator_id", "matched_field", name="uq_ioc_event_match"),
        {"extend_existing": True},
    )
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    indicator_id = Column(
        Integer, ForeignKey("threat_intel.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alert_id = Column(
        Integer, ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    match_type = Column(String(80), nullable=False)
    matched_field = Column(String(120), nullable=False)
    matched_value = Column(String(255), nullable=False)
    confidence = Column(Integer, nullable=False)
    severity = Column(String(80), nullable=False)
    provenance = Column(JSON, default=dict)
    matched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class MITRETechnique(Base):
    __tablename__ = "mitre_techniques"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(80), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    platforms = Column(JSON, default=list)
    data_sources = Column(JSON, default=list)
    detection = Column(Text, nullable=True)
    tactics = Column(JSON, default=list)
    parent_technique_id = Column(String(80), nullable=True, index=True)
    external_url = Column(String(500), nullable=True)
    revoked = Column(Integer, default=0, nullable=False)
    deprecated = Column(Integer, default=0, nullable=False)
    stix_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(80), default="investigation")
    format = Column(String(50), default="markdown")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Investigation(Base):
    __tablename__ = "investigations"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(
        Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id = Column(
        Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    initiated_by = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    provider = Column(String(80), nullable=False, default="fallback")
    model = Column(String(120), nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_category = Column(String(80), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    rerun_of = Column(Integer, ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True)


class InvestigationResult(Base):
    __tablename__ = "investigation_results"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(
        Integer,
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    result = Column(JSON, nullable=False, default=dict)
    evidence_references = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class InvestigationFeedback(Base):
    __tablename__ = "investigation_feedback"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    investigation_id = Column(
        Integer, ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category = Column(String(80), nullable=False)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class RefreshTokenSession(Base):
    __tablename__ = "refresh_token_sessions"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    family_id = Column(String(64), nullable=False, index=True)
    replaced_by_hash = Column(String(64), nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    device = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    actor = Column(String(120), nullable=False)
    action = Column(String(200), nullable=False)
    target_type = Column(String(120), nullable=True)
    target_id = Column(String(120), nullable=True)
    request_id = Column(String(64), nullable=True, index=True)
    outcome = Column(String(20), nullable=False, default="success")
    details = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Configuration(Base):
    __tablename__ = "configurations"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(120), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    query = Column(Text, nullable=False)
    owner = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
