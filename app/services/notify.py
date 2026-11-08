import logging

import httpx

from app.services.sms import send_sms

log = logging.getLogger("findit.notify")


def short_title(title: str) -> str:
    """Keeps SMS short: long item titles are cut to 40 characters."""
    return title if len(title) <= 40 else title[:37] + "..."


def notify(phone: str, message: str) -> None:
    """Best-effort SMS. A failed text must never undo the action that triggered it.

    Only the error class is logged: Arkesel's URL contains the API key and must never reach the logs.
    """
    try:
        send_sms(phone, message)
    except httpx.HTTPError as exc:
        log.warning("SMS notification failed (%s)", type(exc).__name__)
