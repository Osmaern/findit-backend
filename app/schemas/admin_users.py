from datetime import datetime

from pydantic import BaseModel


class UserRow(BaseModel):
    id: int
    full_name: str
    phone: str
    email: str | None
    role: str
    phone_verified: bool
    is_active: bool
    created_at: datetime


class UserCounts(BaseModel):
    total: int
    verified: int
    suspended: int
    staff: int


class ItemCounts(BaseModel):
    open_lost: int
    open_found: int
    returned: int
    closed: int
    removed: int
    expired: int


class ClaimCounts(BaseModel):
    pending: int
    approved: int
    declined: int
    withdrawn: int


class StatsOut(BaseModel):
    users: UserCounts
    items: ItemCounts
    claims: ClaimCounts
    open_reports: int
