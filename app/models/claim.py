from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utc_now
from app.models.item import Item
from app.models.user import User


class Claim(Base):
    """One person's claim on one item. Statuses: pending, approved, declined, withdrawn."""

    __tablename__ = "claims"
    __table_args__ = (UniqueConstraint("item_id", "claimant_id", name="uq_claim_item_claimant"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    claimant_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    message: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    item: Mapped[Item] = relationship()
    claimant: Mapped[User] = relationship()
