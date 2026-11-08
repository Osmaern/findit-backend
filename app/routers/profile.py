import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, utc_now, verify_password
from app.models.user import User
from app.schemas.auth import EMAIL_PATTERN, TokenOut
from app.services.notify import notify

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])

# Phone numbers are not editable here: changing one would need a fresh SMS verification first.


class ProfileIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str | None = None  # empty string or null removes the email

    @field_validator("email")
    @classmethod
    def _check_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip().lower()
        if len(value) > 255 or not EMAIL_PATTERN.match(value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("full_name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) < 2:
            raise ValueError("Enter your full name")
        return value


class PasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class ProfileOut(BaseModel):
    full_name: str
    phone: str
    email: str | None
    role: str


def _out(user: User) -> ProfileOut:
    return ProfileOut(full_name=user.full_name, phone=user.phone, email=user.email, role=user.role)


@router.get("", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user)):
    return _out(user)


@router.put("", response_model=ProfileOut)
def update_profile(body: ProfileIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if body.email and body.email != user.email:
        taken = db.scalar(select(User.id).where(User.email == body.email, User.id != user.id))
        if taken is not None:
            raise HTTPException(status_code=409, detail="That email address is already used by another account")
    user.full_name = body.full_name
    user.email = body.email
    db.commit()
    db.refresh(user)
    return _out(user)


@router.post("/password", response_model=TokenOut)
def change_password(
    body: PasswordIn,
    response: Response,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(user.password_hash, body.current_password):
        raise HTTPException(status_code=400, detail="Your current password is not correct")
    if verify_password(user.password_hash, body.new_password):
        raise HTTPException(status_code=400, detail="Choose a different password")

    user.password_hash = hash_password(body.new_password)
    user.token_version += 1  # signs out every other session, as a reset does
    db.commit()

    # Keep this browser signed in with a fresh token
    token = create_access_token(user.id, user.token_version)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
    )
    background.add_task(
        notify, user.phone, "Your FindIt password was changed. If this was not you, reset it again now."
    )
    return TokenOut(access_token=token)
