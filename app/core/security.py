import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

_hasher = PasswordHasher()  # Argon2id is the default algorithm
_DUMMY_HASH = _hasher.hash("timing-equaliser-not-a-real-password")


def utc_now() -> datetime:
    """Current UTC time as a naive datetime, matching how timestamps are stored."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def dummy_verify(password: str) -> None:
    """Runs a password check against a dummy hash so unknown phone numbers take as long as real ones."""
    verify_password(_DUMMY_HASH, password)


def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(code: str) -> str:
    return hmac.new(settings.secret_key.encode(), code.encode(), hashlib.sha256).hexdigest()


def create_access_token(user_id: int) -> str:
    expires = utc_now() + timedelta(minutes=settings.access_token_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expires}, settings.secret_key, algorithm="HS256")
