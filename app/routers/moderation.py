from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import require_moderator
from app.core.security import utc_now
from app.models.claim import Claim
from app.models.item import Item
from app.models.report import ItemReport
from app.models.user import User
from app.schemas.moderation import ReportIn, ReportOut
from app.services.notify import notify, short_title

router = APIRouter(prefix="/api/v1", tags=["moderation"])


def _open_counts(db: Session, item_ids: list[int]) -> dict[int, int]:
    if not item_ids:
        return {}
    rows = db.execute(
        select(ItemReport.item_id, func.count(ItemReport.id))
        .where(ItemReport.item_id.in_(item_ids), ItemReport.status == "open")
        .group_by(ItemReport.item_id)
    )
    return dict(rows.all())


def _out(report: ItemReport, open_count: int) -> ReportOut:
    return ReportOut(
        id=report.id,
        item_id=report.item_id,
        item_title=report.item.title,
        item_kind=report.item.kind,
        item_status=report.item.status,
        owner_name=report.item.owner.full_name,
        reason=report.reason,
        details=report.details,
        reporter_name=report.reporter.full_name,
        status=report.status,
        created_at=report.created_at,
        handled_at=report.handled_at,
        open_reports_on_item=open_count,
    )


def _open_report(db: Session, report_id: int) -> ItemReport:
    report = db.get(ItemReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "open":
        raise HTTPException(status_code=409, detail="This report has already been handled")
    return report


@router.post("/items/{item_id}/report", status_code=201)
def report_item(
    item_id: int,
    body: ReportIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.user_id == user.id:
        raise HTTPException(status_code=403, detail="You cannot report your own post")
    if item.status != "open" or item.expires_at <= utc_now():
        raise HTTPException(status_code=404, detail="Item not found")
    if db.scalar(select(ItemReport.id).where(ItemReport.item_id == item.id, ItemReport.reporter_id == user.id)):
        raise HTTPException(status_code=409, detail="You have already reported this post")

    db.add(ItemReport(item_id=item.id, reporter_id=user.id, reason=body.reason, details=body.details))
    db.commit()
    return {"message": "Thank you. A moderator will look at this post."}


@router.get("/admin/reports", response_model=list[ReportOut])
def list_reports(
    status: Literal["open", "handled", "all"] = "open",
    db: Session = Depends(get_db),
    _moderator: User = Depends(require_moderator),
):
    stmt = (
        select(ItemReport)
        .order_by(ItemReport.created_at.desc())
        .limit(100)
        .options(selectinload(ItemReport.item).selectinload(Item.owner), selectinload(ItemReport.reporter))
    )
    if status == "open":
        stmt = stmt.where(ItemReport.status == "open")
    elif status == "handled":
        stmt = stmt.where(ItemReport.status != "open")
    reports = db.scalars(stmt).all()
    counts = _open_counts(db, list({report.item_id for report in reports}))
    return [_out(report, counts.get(report.item_id, 0)) for report in reports]


@router.post("/admin/reports/{report_id}/remove", response_model=ReportOut)
def remove_post(
    report_id: int,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    report = _open_report(db, report_id)
    item = report.item
    db.scalar(select(Item.id).where(Item.id == item.id).with_for_update())
    db.refresh(item)

    now = utc_now()
    item.status = "removed"
    for other in db.scalars(select(ItemReport).where(ItemReport.item_id == item.id, ItemReport.status == "open")):
        other.status = "actioned"
        other.handled_by_id = moderator.id
        other.handled_at = now
    waiting = db.scalars(select(Claim).where(Claim.item_id == item.id, Claim.status == "pending")).all()
    for claim in waiting:
        claim.status = "declined"
        claim.decided_at = now
    db.commit()
    db.refresh(report)

    title = short_title(item.title)
    background.add_task(
        notify, item.owner.phone, f'FindIt: your post "{title}" was removed by a moderator because it broke the rules.'
    )
    for claim in waiting:
        background.add_task(notify, claim.claimant.phone, f'FindIt: the post "{title}" was removed by a moderator.')
    return _out(report, 0)


@router.post("/admin/reports/{report_id}/dismiss", response_model=ReportOut)
def dismiss_report(
    report_id: int,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    report = _open_report(db, report_id)
    report.status = "dismissed"
    report.handled_by_id = moderator.id
    report.handled_at = utc_now()
    db.commit()
    db.refresh(report)
    return _out(report, _open_counts(db, [report.item_id]).get(report.item_id, 0))


@router.post("/admin/items/{item_id}/restore")
def restore_post(
    item_id: int,
    db: Session = Depends(get_db),
    _moderator: User = Depends(require_moderator),
):
    """Puts back a post that was removed by mistake."""
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status != "removed":
        raise HTTPException(status_code=409, detail="Only a removed post can be restored")
    item.status = "open"
    db.commit()
    return {"status": item.status}
