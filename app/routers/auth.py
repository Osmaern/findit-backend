import hmac
from datetime import timedelta

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.ratelimit import rate_limit
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
from app.schemas.auth import LoginIn, PhoneIn, RegisterIn, ResetIn, TokenOut, VerifyIn
from app.services.notify import notify
from app.services.sms import send_sms

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

OTP_TTL = timedelta(minutes=10)
OTP_RESEND_WAIT = timedelta(seconds=60)
MAX_OTP_ATTEMPTS = 5
MAX_LOGIN_FAILURES = 5
LOGIN_LOCKOUT = timedelta(minutes=15)
PURPOSE_VERIFY = "verify"
PURPOSE_RESET = "reset"


def _find_user(db: Session, phone: str) -> User | None:
    return db.scalar(select(User).where(User.phone == phone))


def _issue_code(db: Session, user: User, purpose: str) -> str:
    code = generate_otp()
    # Any earlier unused code of the same kind stops working as soon as a new one is issued
    db.query(OTPCode).filter(
        OTPCode.user_id == user.id, OTPCode.purpose == purpose, OTPCode.used.is_(False)
    ).update({"used": True})
    db.add(OTPCode(user_id=user.id, purpose=purpose, code_hash=hash_otp(code), expires_at=utc_now() + OTP_TTL))
    db.commit()
    return code


def _send_new_code(db: Session, user: User) -> None:
    code = _issue_code(db, user, PURPOSE_VERIFY)
    try:
        send_sms(user.phone, f"Your FindIt code is {code}. It expires in 10 minutes.")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Could not send the code. Please try again.")


@router.post("/register", status_code=201, dependencies=[Depends(rate_limit("register", 20, 600))])
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if _find_user(db, body.phone):
        raise HTTPException(status_code=409, detail="This phone number is already registered")
    if body.email and db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(status_code=409, detail="This email is already registered")
    user = User(
        full_name=body.full_name,
        phone=body.phone,
        email=body.email,
        password_hash=hash_password(body.password),
        phone_verified=False,
        is_active=False,
        terms_accepted_at=utc_now(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _send_new_code(db, user)
    return {"message": "Verification code sent"}


@router.post("/verify-phone", dependencies=[Depends(rate_limit("verify-phone", 30, 600))])
def verify_phone(body: VerifyIn, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=400, detail="Incorrect or expired code")
    user = _find_user(db, body.phone)
    if user is None or user.phone_verified:
        raise invalid

    otp = db.scalar(
        select(OTPCode)
        .where(OTPCode.user_id == user.id, OTPCode.purpose == PURPOSE_VERIFY, OTPCode.used.is_(False))
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


@router.post("/resend-code", dependencies=[Depends(rate_limit("resend-code", 10, 600))])
def resend_code(body: PhoneIn, db: Session = Depends(get_db)):
    reply = {"message": "If the number is registered, a new code has been sent"}
    user = _find_user(db, body.phone)
    if user is None or user.phone_verified:
        return reply
    last = db.scalar(
        select(OTPCode)
        .where(OTPCode.user_id == user.id, OTPCode.purpose == PURPOSE_VERIFY)
        .order_by(OTPCode.id.desc())
    )
    if last and utc_now() - last.created_at < OTP_RESEND_WAIT:
        raise HTTPException(status_code=429, detail="Please wait a minute before requesting another code")
    _send_new_code(db, user)
    return reply


@router.post("/forgot-password", dependencies=[Depends(rate_limit("forgot-password", 10, 600))])
def forgot_password(body: PhoneIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    # The answer is the same whether or not the number has an account, so nobody can use this to find out.
    reply = {"message": "If the number belongs to an account, a reset code has been sent"}
    user = _find_user(db, body.phone)
    if user is None or not user.phone_verified or not user.is_active:
        return reply
    last = db.scalar(
        select(OTPCode)
        .where(OTPCode.user_id == user.id, OTPCode.purpose == PURPOSE_RESET)
        .order_by(OTPCode.id.desc())
    )
    if last and utc_now() - last.created_at < OTP_RESEND_WAIT:
        return reply  # ignored quietly: an error here would reveal that the account exists
    code = _issue_code(db, user, PURPOSE_RESET)
    background.add_task(
        notify,
        user.phone,
        f"Your FindIt password reset code is {code}. It expires in 10 minutes. "
        "If you did not ask for it, ignore this message.",
    )
    return reply


@router.post("/reset-password", dependencies=[Depends(rate_limit("reset-password", 20, 600))])
def reset_password(body: ResetIn, background: BackgroundTasks, db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=400, detail="Incorrect or expired code")
    user = _find_user(db, body.phone)
    if user is None or not user.phone_verified or not user.is_active:
        raise invalid

    otp = db.scalar(
        select(OTPCode)
        .where(OTPCode.user_id == user.id, OTPCode.purpose == PURPOSE_RESET, OTPCode.used.is_(False))
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

    user.password_hash = hash_password(body.new_password)
    user.token_version += 1  # signs out every session issued before this password change
    user.failed_logins = 0
    user.locked_until = None
    db.query(OTPCode).filter(
        OTPCode.user_id == user.id, OTPCode.purpose == PURPOSE_RESET, OTPCode.used.is_(False)
    ).update({"used": True})
    db.commit()
    background.add_task(
        notify, user.phone, "Your FindIt password was changed. If this was not you, reset it again now."
    )
    return {"message": "Password changed. You can now log in."}


@router.post("/login", response_model=TokenOut, dependencies=[Depends(rate_limit("login", 30, 60))])
def login(body: LoginIn, response: Response, db: Session = Depends(get_db)):
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
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been suspended")
    if not user.phone_verified:
        raise HTTPException(status_code=403, detail="Verify your phone number before logging in")

    user.failed_logins = 0
    user.locked_until = None
    db.commit()
    token = create_access_token(user.id, user.token_version)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=settings.access_token_minutes * 60,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
    )
    return TokenOut(access_token=token)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", httponly=True, samesite="lax")
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "email": user.email,
        "role": user.role,
    }
