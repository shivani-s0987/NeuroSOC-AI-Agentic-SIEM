import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import PasswordResetToken, RefreshTokenSession, User
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserOut,
)
from app.security import (
    create_token,
    decode_token,
    get_current_user,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.core.rate_limit import check_rate_limit
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_session(db: Session, user: User, family_id: str | None = None) -> Token:
    family_id = family_id or uuid.uuid4().hex
    refresh = create_token(str(user.username), str(user.role), refresh=True, family_id=family_id)
    db.add(
        RefreshTokenSession(
            user_id=user.id,
            token_hash=token_hash(refresh),
            family_id=family_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_expiry_days),
        )
    )
    db.commit()
    return Token(
        access_token=create_token(str(user.username), str(user.role)), refresh_token=refresh
    )


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, request: Request, db: Session = Depends(get_db)) -> User:
    check_rate_limit(
        f"register:{request.client.host if request.client else 'unknown'}",
        settings.auth_rate_limit_per_minute,
    )
    if (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    ):
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="SECURITY_VIEWER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    check_rate_limit(
        f"login:{request.client.host if request.client else 'unknown'}",
        settings.auth_rate_limit_per_minute,
    )
    user = db.query(User).filter(User.username == payload.username).first()
    if (
        user is None
        or bool(user.disabled)
        or not verify_password(payload.password, str(user.password_hash))
    ):
        record_audit(
            db,
            payload.username,
            "login",
            outcome="denied",
            details={"reason": "invalid credentials"},
            request_id=request.headers.get("X-Request-ID"),
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if needs_rehash(str(user.password_hash)):
        user.password_hash = hash_password(payload.password)
        db.commit()
    token = issue_session(db, user)
    record_audit(
        db,
        str(user.username),
        "login",
        outcome="success",
        actor_user_id=user.id,
        request_id=request.headers.get("X-Request-ID"),
    )
    return token


@router.post("/refresh", response_model=Token)
def refresh(
    payload: RefreshRequest | None = None,
    refresh_token: str | None = None,
    db: Session = Depends(get_db),
) -> Token:
    supplied = payload.refresh_token if payload else refresh_token
    if not supplied:
        raise HTTPException(status_code=422, detail="Refresh token is required")
    try:
        claims = decode_token(supplied, refresh=True)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    session = (
        db.query(RefreshTokenSession)
        .filter(RefreshTokenSession.token_hash == token_hash(supplied))
        .first()
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if session.revoked_at or session.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(
        timezone.utc
    ):
        db.query(RefreshTokenSession).filter(
            RefreshTokenSession.family_id == session.family_id
        ).update({RefreshTokenSession.revoked_at: datetime.now(timezone.utc)})
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token reuse is not allowed")
    user = db.query(User).filter(User.id == session.user_id, User.disabled == 0).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    session.revoked_at = datetime.now(timezone.utc)
    rotated = issue_session(db, user, str(claims["family_id"]))
    session.replaced_by_hash = token_hash(rotated.refresh_token)
    db.commit()
    return rotated


@router.post("/logout")
def logout(
    payload: RefreshRequest | None = None,
    refresh_token: str | None = None,
    db: Session = Depends(get_db),
) -> dict[str, bool]:
    supplied = payload.refresh_token if payload else refresh_token
    if supplied:
        session = (
            db.query(RefreshTokenSession)
            .filter(RefreshTokenSession.token_hash == token_hash(supplied))
            .first()
        )
        if session:
            db.query(RefreshTokenSession).filter(
                RefreshTokenSession.family_id == session.family_id
            ).update({RefreshTokenSession.revoked_at: datetime.now(timezone.utc)})
            db.commit()
    return {"logged_out": True}


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> dict[str, str]:
    user = db.query(User).filter(User.email == payload.email).first()
    response = {"message": "If the account exists, password reset instructions have been prepared."}
    if user:
        raw = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=token_hash(raw),
                expires_at=datetime.now(timezone.utc)
                + timedelta(minutes=settings.password_reset_expiry_minutes),
            )
        )
        db.commit()
        if settings.app_env in {"development", "testing"}:
            response["development_token"] = raw
    return response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    reset = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash(payload.token))
        .first()
    )
    if (
        reset is None
        or reset.used_at is not None
        or reset.expires_at.replace(tzinfo=timezone.utc) <= datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")
    user = db.query(User).filter(User.id == reset.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired")
    user.password_hash = hash_password(payload.password)
    reset.used_at = datetime.now(timezone.utc)
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
    ).update({PasswordResetToken.used_at: datetime.now(timezone.utc)})
    db.query(RefreshTokenSession).filter(
        RefreshTokenSession.user_id == user.id, RefreshTokenSession.revoked_at.is_(None)
    ).update({RefreshTokenSession.revoked_at: datetime.now(timezone.utc)})
    db.commit()
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
