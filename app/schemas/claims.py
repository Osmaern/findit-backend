from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ClaimIn(BaseModel):
    message: str = Field(max_length=500)

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise ValueError("Please describe why this item is yours (at least 10 characters)")
        return value


class ClaimMineOut(BaseModel):
    """A claim as its claimant sees it."""

    id: int
    item_id: int
    item_title: str
    item_kind: str
    item_status: str
    message: str
    status: str
    created_at: datetime
    decided_at: datetime | None
    contact_phone: str | None = None  # owner's phone: only after approval, and only if the owner allowed contact


class ClaimReceivedOut(BaseModel):
    """A claim as the item's owner sees it."""

    id: int
    item_id: int
    item_title: str
    item_kind: str
    item_status: str
    claimant_name: str
    message: str
    status: str
    created_at: datetime
    decided_at: datetime | None
    claimant_phone: str | None = None  # only after the owner approves the claim
