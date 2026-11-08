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


def create_access_token(user_id: int, token_version: int) -> str:
    """The token carries the account's token version. Changing the version signs out every token issued before."""
    expires = utc_now() + timedelta(minutes=settings.access_token_minutes)
    claims = {"sub": str(user_id), "ver": token_version, "exp": expires}
    return jwt.encode(claims, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> tuple[int, int] | None:
    """Returns (user id, token version), or None if the token is invalid or expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(payload["sub"]), int(payload["ver"])
    except (jwt.InvalidTokenError, KeyError, ValueError, TypeError):
        return None
