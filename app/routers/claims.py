from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.ratelimit import rate_limit
from app.core.security import utc_now
from app.models.claim import Claim
from app.models.item import Item
from app.models.user import User
from app.schemas.claims import ClaimIn, ClaimMineOut, ClaimReceivedOut
from app.services.notify import notify, short_title

router = APIRouter(prefix="/api/v1", tags=["claims"])

MAX_PENDING_PER_USER = 10  # stops one account from flooding owners with SMS


def _mine_out(claim: Claim) -> ClaimMineOut:
    item = claim.item
    show_contact = claim.status == "approved" and item.allow_contact
    return ClaimMineOut(
        id=claim.id,
        item_id=item.id,
        item_title=item.title,
        item_kind=item.kind,
        item_status=item.status,
        message=claim.message,
        status=claim.status,
        created_at=claim.created_at,
        decided_at=claim.decided_at,
        contact_phone=item.owner.phone if show_contact else None,
    )


def _received_out(claim: Claim) -> ClaimReceivedOut:
    item = claim.item
    return ClaimReceivedOut(
        id=claim.id,
        item_id=item.id,
        item_title=item.title,
        item_kind=item.kind,
        item_status=item.status,
        claimant_name=claim.claimant.full_name,
        message=claim.message,
        status=claim.status,
        created_at=claim.created_at,
        decided_at=claim.decided_at,
        claimant_phone=claim.claimant.phone if claim.status == "approved" else None,
    )


def _owned_pending_claim(db: Session, claim_id: int, owner: User) -> Claim:
    """Loads a pending claim on one of the owner's items, locking the item row while we decide."""
    claim = db.get(Claim, claim_id)
    if claim is None or claim.item.user_id != owner.id:
        raise HTTPException(status_code=404, detail="Claim not found")
    db.scalar(select(Item.id).where(Item.id == claim.item_id).with_for_update())
    db.refresh(claim)
    if claim.status != "pending":
        raise HTTPException(status_code=409, detail="This claim has already been decided")
    return claim


@router.post(
    "/items/{item_id}/claims",
    status_code=201,
    response_model=ClaimMineOut,
    dependencies=[Depends(rate_limit("claim-create", 30, 3600))],
)
def create_claim(
    item_id: int,
    body: ClaimIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot claim your own report")
    # Only open, unexpired items can be claimed. Anything else looks the same as "does not exist".
    if item.status != "open" or item.expires_at <= utc_now():
        raise HTTPException(status_code=404, detail="Item not found")

    already = db.scalar(select(Claim.id).where(Claim.item_id == item.id, Claim.claimant_id == user.id))
    if already is not None:
        raise HTTPException(status_code=409, detail="You have already claimed this item")

    pending = db.scalar(
        select(func.count(Claim.id)).where(Claim.claimant_id == user.id, Claim.status == "pending")
    )
    if pending >= MAX_PENDING_PER_USER:
        raise HTTPException(status_code=429, detail="You have too many pending claims. Wait for some to be answered.")

    claim = Claim(item_id=item.id, claimant_id=user.id, message=body.message)
    db.add(claim)
    db.commit()
    db.refresh(claim)

    background.add_task(
        notify,
        item.owner.phone,
        f'FindIt: someone has claimed your item "{short_title(item.title)}". Log in to FindIt to review it.',
    )
    return _mine_out(claim)


@router.get("/claims/mine", response_model=list[ClaimMineOut])
def my_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = (
        select(Claim)
        .where(Claim.claimant_id == user.id)
        .order_by(Claim.created_at.desc())
        .options(selectinload(Claim.item))
    )
    return [_mine_out(claim) for claim in db.scalars(stmt)]


@router.get("/claims/received", response_model=list[ClaimReceivedOut])
def received_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = (
        select(Claim)
        .join(Item, Claim.item_id == Item.id)
        .where(Item.user_id == user.id)
        .order_by(Claim.created_at.desc())
        .options(selectinload(Claim.item), selectinload(Claim.claimant))
    )
    return [_received_out(claim) for claim in db.scalars(stmt)]


@router.post("/claims/{claim_id}/approve", response_model=ClaimReceivedOut)
def approve_claim(
    claim_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    claim = _owned_pending_claim(db, claim_id, user)
    item = claim.item
    if item.status != "open":
        raise HTTPException(status_code=409, detail="This item already has an approved claim")

    now = utc_now()
    claim.status = "approved"
    claim.decided_at = now
    item.status = "claim_pending"
    # Only one claim can win. The others are closed so nobody waits for an answer that will not come.
    others = db.scalars(
        select(Claim).where(Claim.item_id == item.id, Claim.id != claim.id, Claim.status == "pending")
    ).all()
    for other in others:
        other.status = "declined"
        other.decided_at = now
    db.commit()
    db.refresh(claim)

    background.add_task(
        notify,
        claim.claimant.phone,
        f'FindIt: your claim for "{short_title(item.title)}" was approved. Log in to FindIt to see the next step.',
    )
    for other in others:
        background.add_task(
            notify,
            other.claimant.phone,
            f'FindIt: your claim for "{short_title(item.title)}" was not successful.',
        )
    return _received_out(claim)


@router.post("/claims/{claim_id}/decline", response_model=ClaimReceivedOut)
def decline_claim(
    claim_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    claim = _owned_pending_claim(db, claim_id, user)
    claim.status = "declined"
    claim.decided_at = utc_now()
    db.commit()
    db.refresh(claim)
    background.add_task(
        notify,
        claim.claimant.phone,
        f'FindIt: your claim for "{short_title(claim.item.title)}" was not successful.',
    )
    return _received_out(claim)


@router.post("/claims/{claim_id}/withdraw", response_model=ClaimMineOut)
def withdraw_claim(claim_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    claim = db.get(Claim, claim_id)
    if claim is None or claim.claimant_id != user.id:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status != "pending":
        raise HTTPException(status_code=409, detail="Only a pending claim can be withdrawn")
    claim.status = "withdrawn"
    claim.decided_at = utc_now()
    db.commit()
    db.refresh(claim)
    return _mine_out(claim)


@router.post("/items/{item_id}/returned")
def mark_returned(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status != "claim_pending":
        raise HTTPException(status_code=409, detail="Approve a claim first")
    item.status = "returned"
    db.commit()
    return {"status": item.status}
