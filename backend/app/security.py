import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User

_passwords = PasswordHasher()
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return _passwords.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith("$argon2"):
        try:
            return _passwords.verify(hashed, password)
        except VerifyMismatchError:
            return False
    if len(hashed) == 64:
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    return False


def needs_rehash(hashed: str) -> bool:
    return not hashed.startswith("$argon2") or _passwords.check_needs_rehash(hashed)


def create_token(subject: str, role: str, refresh: bool = False) -> str:
    now = datetime.now(timezone.utc)
    lifetime = timedelta(days=settings.refresh_expiry_days) if refresh else timedelta(minutes=settings.jwt_expiry_minutes)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
        "jti": uuid.uuid4().hex,
        "type": "refresh" if refresh else "access",
    }
    secret = settings.jwt_refresh_secret if refresh else settings.jwt_secret
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, refresh: bool = False) -> dict[str, Any]:
    secret = settings.jwt_refresh_secret if refresh else settings.jwt_secret
    payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    expected_type = "refresh" if refresh else "access"
    if payload.get("type", "access") != expected_type:
        raise jwt.InvalidTokenError("Unexpected token type")
    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from None
    user = db.query(User).filter(User.username == payload["sub"], User.disabled.is_(False)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*allowed_roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if str(user.role) not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return dependency
