from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
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
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    rule_id = Column(String(120), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    enabled = Column(Integer, default=1)
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
    intel_type = Column(String(80), default="ip")
    severity = Column(String(80), default="medium")
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class MITRETechnique(Base):
    __tablename__ = "mitre_techniques"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    technique_id = Column(String(80), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
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


class RefreshTokenSession(Base):
    __tablename__ = "refresh_token_sessions"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
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
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {"extend_existing": True}
    id = Column(Integer, primary_key=True, index=True)
    actor_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
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
