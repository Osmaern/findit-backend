from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

Category = Literal["phone", "bag", "wallet", "keys", "id_card", "electronics", "clothing", "books", "other"]


class ItemIn(BaseModel):
    kind: Literal["lost", "found"]
    title: str = Field(min_length=3, max_length=120)
    category: Category
    location: str = Field(min_length=2, max_length=120)
    description: str = Field(min_length=10, max_length=1000)
    event_date: date
    private_detail: str | None = Field(default=None, max_length=500)
    allow_contact: bool = False

    @model_validator(mode="after")
    def _check_rules(self):
        if self.event_date > date.today():
            raise ValueError("The date cannot be in the future")
        if self.kind == "found" and not (self.private_detail and self.private_detail.strip()):
            raise ValueError("Found items need a private verification detail that only you can see")
        return self


class ItemOut(BaseModel):
    id: int
    kind: str
    title: str
    category: str
    location: str
    description: str
    event_date: date
    status: str
    allow_contact: bool
    created_at: datetime
    photo_ids: list[int]
    is_owner: bool = False  # true when the person asking owns this item
    private_detail: str | None = None  # set only for the item's owner


class MyItemOut(ItemOut):
    """An item as listed on its owner's My Posts page."""

    pending_claims: int = 0
