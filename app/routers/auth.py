import hmac
from datetime import timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    dummy_verify,
    generate_otp,
    hash_otp,
    hash_password,
    utc_now,
    verify_password,
)
from app.models.otp import OTPCode
from app.models.user import User
from app.schemas.auth import LoginIn, PhoneIn, RegisterIn, TokenOut, VerifyIn
from app.services.sms import send_sms

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

OTP_TTL = timedelta(minutes=10)
OTP_RESEND_WAIT = timedelta(seconds=60)
MAX_OTP_ATTEMPTS = 5
MAX_LOGIN_FAILURES = 5
LOGIN_LOCKOUT = timedelta(minutes=15)


def _find_user(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))


def _send_new_code(db: Session, user: User) -> None:
    code = generate_otp()
    # Any earlier unused code stops working as soon as a new one is issued
    db.query(OTPCode).filter(OTPCode.user_id == user.id, OTPCode.used.is_(False)).update({"used": True})
    db.add(OTPCode(user_id=user.id, code_hash=hash_otp(code), expires_at=utc_now() + OTP_TTL))
    db.commit()
    try:
        send_sms(user.phone, f"Your FindIt code is {code}. It expires in 10 minutes.")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not send the code. Please try again.")


@router.post("/register", status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if _find_user(db, body.phone):
        raise HTTPException(status_code=409, detail="This phone number is already registered")
    user = User(
        full_name=body.full_name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        phone_verified=False,
        is_active=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _send_new_code(db, user)
    return {"message": "Verification code sent"}


@router.post("/verify-phone")
def verify_phone(body: VerifyIn, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=400, detail="Incorrect or expired code")
    user = _find_user(db, body.phone)
    if user is None or user.phone_verified:
        raise invalid

    otp = db.scalar(
        select(OTPCode)
        .where(OTPCode.user_id == user.id, OTPCode.used.is_(False))
        .order_by(OTPCode.id.desc())
    )
    if otp is None or otp.expires_at < utc_now():
        raise invalid
    if otp.attempts >= MAX_OTP_ATTEMPTS:
        otp.used = True
        db.commit()
        raise HTTPException(status_code=429, detail="Too many attempts. Request a new code.")
    if not hmac.compare_digest(otp.code_hash, hash_otp(body.code)):
        otp.attempts += 1
        db.commit()
        raise invalid

    otp.used = True
    user.phone_verified = True
    user.is_active = True
    db.commit()
    return {"message": "Phone verified. You can now log in."}


@router.post("/resend-code")
def resend_code(body: PhoneIn, db: Session = Depends(get_db)):
    reply = {"message": "If the number is registered, a new code has been sent"}
    user = _find_user(db, body.phone)
    if user is None or user.phone_verified:
        return reply
    last = db.scalar(
        select(OTPCode).where(OTPCode.user_id == user.id).order_by(OTPCode.id.desc())
    )
    if last and utc_now() - last.created_at < OTP_RESEND_WAIT:
        raise HTTPException(status_code=429, detail="Please wait a minute before requesting another code")
    _send_new_code(db, user)
    return reply


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    wrong = HTTPException(status_code=401, detail="Invalid phone or password")
    user = _find_user(db, body.phone)
    if user is None:
        dummy_verify(body.password)
        raise wrong
    if user.locked_until and user.locked_until > utc_now():
        raise HTTPException(status_code=423, detail="Account temporarily locked. Try again later.")
    if not verify_password(user.password_hash, body.password):
        user.failed_logins += 1
        if user.failed_logins >= MAX_LOGIN_FAILURES:
            user.locked_until = utc_now() + LOGIN_LOCKOUT
            user.failed_logins = 0
        db.commit()
        raise wrong
    if not user.phone_verified or not user.is_active:
        raise HTTPException(status_code=403, detail="Verify your phone number before logging in")

    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    return TokenOut(access_token=create_access_token(user.id))
