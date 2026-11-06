from fastapi import Cookie, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User


def _user_from_request(authorization: str | None, access_token: str | None, db: Session) -> User | None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif access_token:
        token = access_token
    if not token:
        return None
    user_id = decode_access_token(token)
    if user_id is None:
        return None
    user = db.get(User, user_id)
    if user is None or not user.is_active or not user.phone_verified:
        return None
    return user


def get_optional_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    return _user_from_request(authorization, access_token, db)


def get_current_user(
    authorization: str | None = Header(default=None),
    access_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> User:
    user = _user_from_request(authorization, access_token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Please log in again")
    return user
