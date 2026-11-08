from fastapi import Depends, HTTPException

from app.core.deps import get_current_user
from app.models.user import User

MODERATOR_ROLES = ("moderator", "admin")


def require_moderator(user: User = Depends(get_current_user)) -> User:
    """Only moderators and admins may pass. Everyone else gets 403."""
    if user.role not in MODERATOR_ROLES:
        raise HTTPException(status_code=403, detail="Moderators only")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Only admins may pass. Moderators and members get 403."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user
