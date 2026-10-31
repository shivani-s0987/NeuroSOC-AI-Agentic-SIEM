import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, Token, UserCreate, UserOut
from app.security import (
    create_token,
    decode_token,
    get_current_user,
    hash_password,
    needs_rehash,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if (
        db.query(User)
        .filter((User.username == payload.username) | (User.email == payload.email))
        .first()
    ):
        raise HTTPException(status_code=400, detail="User already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role="Viewer" if payload.role not in {"Administrator", "Analyst"} else "Viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.username == payload.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    password_hash = user.password_hash
    if not verify_password(payload.password, str(password_hash)):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if needs_rehash(str(user.password_hash)):
        user.password_hash = hash_password(payload.password)
        db.commit()
    username = str(user.username)
    role = str(user.role)
    return Token(
        access_token=create_token(username, role),
        refresh_token=create_token(username, role, refresh=True),
    )


@router.post("/refresh", response_model=Token)
def refresh(refresh_token: str, db: Session = Depends(get_db)) -> Token:
    try:
        payload = decode_token(refresh_token, refresh=True)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    user = db.query(User).filter(User.username == payload["sub"], User.disabled.is_(False)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return Token(
        access_token=create_token(str(user.username), str(user.role)),
        refresh_token=create_token(str(user.username), str(user.role), refresh=True),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
