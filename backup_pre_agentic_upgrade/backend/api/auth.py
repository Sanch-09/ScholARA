"""
ScholARA — Auth API Routes
POST /auth/register
POST /auth/login
GET  /auth/me
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator

from backend.core.database import get_db
from backend.core.security import (
    hash_password, verify_password,
    create_access_token, get_current_user,
)
from backend.core.config import settings
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Pydantic Schemas ──────────────────────────────────────────

class LoginRequest(BaseModel):
    email: str       # accepts email OR username
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str = ""

    @field_validator("username")
    @classmethod
    def username_valid(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, _ and -")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strong(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool
    is_admin: bool

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────

@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check uniqueness
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Issue token
    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/username and password (JSON body)."""
    identifier = (data.email or "").strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )

    # Case-insensitive match (emails + stored lowercase usernames)
    user = (
        db.query(User)
        .filter(func.lower(User.email) == func.lower(identifier))
        .first()
        or db.query(User)
        .filter(func.lower(User.username) == func.lower(identifier))
        .first()
    )

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        username=user.username,
        email=user.email,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return current_user
