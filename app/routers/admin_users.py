import re

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_admin
from app.core.security import utc_now
from app.models.claim import Claim
from app.models.item import Item
from app.models.report import ItemReport
from app.models.user import User
from app.schemas.admin_users import ClaimCounts, ItemCounts, StatsOut, UserCounts, UserRow
from app.services.notify import notify

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _row_count(db: Session, model, *conditions) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*conditions)) or 0


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    now = utc_now()
    open_now = (Item.status == "open", Item.expires_at > now)
    return StatsOut(
        users=UserCounts(
            total=_row_count(db, User),
            verified=_row_count(db, User, User.phone_verified.is_(True)),
            suspended=_row_count(db, User, User.is_active.is_(False)),
            staff=_row_count(db, User, User.role.in_(("moderator", "admin"))),
        ),
        items=ItemCounts(
            open_lost=_row_count(db, Item, Item.kind == "lost", *open_now),
            open_found=_row_count(db, Item, Item.kind == "found", *open_now),
            returned=_row_count(db, Item, Item.status == "returned"),
            closed=_row_count(db, Item, Item.status == "closed"),
            removed=_row_count(db, Item, Item.status == "removed"),
            expired=_row_count(db, Item, Item.status == "open", Item.expires_at <= now),
        ),
        claims=ClaimCounts(
            pending=_row_count(db, Claim, Claim.status == "pending"),
            approved=_row_count(db, Claim, Claim.status == "approved"),
            declined=_row_count(db, Claim, Claim.status == "declined"),
            withdrawn=_row_count(db, Claim, Claim.status == "withdrawn"),
        ),
        open_reports=_row_count(db, ItemReport, ItemReport.status == "open"),
    )


@router.get("/users", response_model=list[UserRow])
def list_users(
    q: str | None = Query(default=None, max_length=80),
    status: str = Query(default="all", pattern="^(all|suspended)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    stmt = select(User).order_by(User.created_at.desc(), User.id.desc()).limit(limit).offset(offset)
    if q and q.strip():
        text = q.strip()
        pattern = f"%{text}%"
        matches = [User.full_name.ilike(pattern), User.phone.ilike(pattern), User.email.ilike(pattern)]
        digits = re.sub(r"\D", "", text)
        if digits.startswith("0") and len(digits) > 1:
            matches.append(User.phone.ilike(f"%233{digits[1:]}%"))  # numbers are stored as 233..., people type 0...
        stmt = stmt.where(or_(*matches))
    if status == "suspended":
        stmt = stmt.where(User.is_active.is_(False))
    return [UserRow.model_validate(user, from_attributes=True) for user in db.scalars(stmt)]


def _target(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/users/{user_id}/suspend", response_model=UserRow)
def suspend_user(
    user_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = _target(db, user_id)
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot suspend your own account")
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="An admin cannot be suspended here")
    if not user.is_active:
        raise HTTPException(status_code=409, detail="This account is already suspended")
    user.is_active = False
    user.token_version += 1  # old sessions stay dead even if the account is restored later
    db.commit()
    db.refresh(user)
    background.add_task(notify, user.phone, "FindIt: your account has been suspended for breaking the rules.")
    return UserRow.model_validate(user, from_attributes=True)


@router.post("/users/{user_id}/restore", response_model=UserRow)
def restore_user(
    user_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    user = _target(db, user_id)
    if user.is_active:
        raise HTTPException(status_code=409, detail="This account is not suspended")
    user.is_active = True
    db.commit()
    db.refresh(user)
    background.add_task(notify, user.phone, "FindIt: your account has been restored. You can log in again.")
    return UserRow.model_validate(user, from_attributes=True)
