from datetime import date, datetime, timedelta

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utc_now

ITEM_LIFETIME = timedelta(days=60)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10), index=True)  # lost | found
    title: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40), index=True)
    location: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text)
    event_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="open", server_default="open", index=True)
    allow_contact: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: utc_now() + ITEM_LIFETIME)

    owner: Mapped["User"] = relationship("User")
    private: Mapped["ItemPrivate | None"] = relationship(
        back_populates="item", cascade="all, delete-orphan", uselist=False
    )
    photos: Mapped[list["ItemPhoto"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemPhoto.position"
    )


class ItemPrivate(Base):
    """Verification detail. Never returned to anyone except the item's owner."""

    __tablename__ = "item_private"

    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), primary_key=True)
    detail: Mapped[str] = mapped_column(String(500))
    item: Mapped[Item] = relationship(back_populates="private")


class ItemPhoto(Base):
    __tablename__ = "item_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(80), unique=True)
    content_type: Mapped[str] = mapped_column(String(30))
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    item: Mapped[Item] = relationship(back_populates="photos")
