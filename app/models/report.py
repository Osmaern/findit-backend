from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.security import utc_now
from app.models.item import Item
from app.models.user import User


class ItemReport(Base):
    """A member's complaint about a post. Statuses: open, actioned (post removed), dismissed."""

    __tablename__ = "item_reports"
    __table_args__ = (UniqueConstraint("item_id", "reporter_id", name="uq_report_item_reporter"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reason: Mapped[str] = mapped_column(String(20))  # spam | inappropriate | fake | other
    details: Mapped[str] = mapped_column(String(300), default="", server_default="")
    status: Mapped[str] = mapped_column(String(20), default="open", server_default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    handled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    item: Mapped[Item] = relationship()
    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    handled_by: Mapped[User | None] = relationship(foreign_keys=[handled_by_id])
