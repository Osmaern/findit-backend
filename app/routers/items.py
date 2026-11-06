import secrets
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_user
from app.core.security import utc_now
from app.models.item import Item, ItemPhoto, ItemPrivate
from app.models.user import User
from app.schemas.items import ItemIn, ItemOut

router = APIRouter(prefix="/api/v1/items", tags=["items"])

UPLOAD_DIR = Path(settings.upload_dir)
MAX_PHOTOS_PER_ITEM = 2
MAX_PAGE_SIZE = 50
EXTENSIONS = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


def _detect_image_type(head: bytes) -> str | None:
    """Checks the real file signature, not the name or the type the browser claims."""
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    return None


def _is_visible(item: Item, viewer: User | None) -> bool:
    if viewer is not None and viewer.id == item.user_id:
        return True
    return item.status == "open" and item.expires_at > utc_now()


def _to_out(item: Item, viewer: User | None) -> ItemOut:
    is_owner = viewer is not None and viewer.id == item.user_id
    return ItemOut(
        id=item.id,
        kind=item.kind,
        title=item.title,
        category=item.category,
        location=item.location,
        description=item.description,
        event_date=item.event_date,
        status=item.status,
        allow_contact=item.allow_contact,
        created_at=item.created_at,
        photo_ids=[photo.id for photo in item.photos],
        private_detail=item.private.detail if (is_owner and item.private) else None,
    )


@router.post("", status_code=201, response_model=ItemOut)
def create_item(body: ItemIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = Item(
        user_id=user.id,
        kind=body.kind,
        title=body.title.strip(),
        category=body.category,
        location=body.location.strip(),
        description=body.description.strip(),
        event_date=body.event_date,
        allow_contact=body.allow_contact,
    )
    if body.private_detail and body.private_detail.strip():
        item.private = ItemPrivate(detail=body.private_detail.strip())
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_out(item, user)


@router.get("", response_model=list[ItemOut])
def list_items(
    kind: Literal["lost", "found"] | None = None,
    category: str | None = Query(default=None, max_length=40),
    location: str | None = Query(default=None, max_length=120),
    q: str | None = Query(default=None, max_length=80),
    limit: int = Query(default=20, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Item).where(Item.status == "open", Item.expires_at > utc_now())
    if kind:
        stmt = stmt.where(Item.kind == kind)
    if category:
        stmt = stmt.where(Item.category == category)
    if location:
        stmt = stmt.where(Item.location == location)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Item.title.ilike(pattern) | Item.description.ilike(pattern))
    stmt = (
        stmt.order_by(Item.created_at.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(Item.photos))
    )
    return [_to_out(item, None) for item in db.scalars(stmt)]


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    item = db.get(Item, item_id)
    if item is None or not _is_visible(item, viewer):
        raise HTTPException(status_code=404, detail="Item not found")
    return _to_out(item, viewer)


@router.post("/{item_id}/photos", status_code=201)
def upload_photo(
    item_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Item, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")

    count = db.scalar(select(func.count(ItemPhoto.id)).where(ItemPhoto.item_id == item.id))
    if count >= MAX_PHOTOS_PER_ITEM:
        raise HTTPException(status_code=409, detail="An item can have at most 2 photos")

    data = file.file.read(settings.max_photo_bytes + 1)
    if len(data) > settings.max_photo_bytes:
        raise HTTPException(status_code=413, detail="Photo is too large (maximum 3 MB)")
    content_type = _detect_image_type(data[:12])
    if content_type is None:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WEBP images are allowed")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    file_name = secrets.token_hex(16) + EXTENSIONS[content_type]
    (UPLOAD_DIR / file_name).write_bytes(data)

    photo = ItemPhoto(item_id=item.id, file_name=file_name, content_type=content_type, position=count)
    db.add(photo)
    db.commit()
    return {"id": photo.id}


@router.get("/{item_id}/photos/{photo_id}")
def get_photo(
    item_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    item = db.get(Item, item_id)
    photo = db.scalar(select(ItemPhoto).where(ItemPhoto.id == photo_id, ItemPhoto.item_id == item_id))
    if item is None or photo is None or not _is_visible(item, viewer):
        raise HTTPException(status_code=404, detail="Photo not found")
    path = UPLOAD_DIR / photo.file_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(path, media_type=photo.content_type)
