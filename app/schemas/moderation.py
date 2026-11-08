from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Reason = Literal["spam", "inappropriate", "fake", "other"]


class ReportIn(BaseModel):
    reason: Reason
    details: str = Field(default="", max_length=300)

    @field_validator("details")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class ReportOut(BaseModel):
    id: int
    item_id: int
    item_title: str
    item_kind: str
    item_status: str
    owner_name: str
    reason: str
    details: str
    reporter_name: str
    status: str
    created_at: datetime
    handled_at: datetime | None
    open_reports_on_item: int  # how many people are waiting on this same post
