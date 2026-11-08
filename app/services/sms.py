import logging

import httpx

from app.core.config import settings

ARKESEL_SMS_URL = "https://sms.arkesel.com/sms/api"
LOW_BALANCE = 20  # warn in the logs when fewer credits than this are left

log = logging.getLogger("findit.sms")


def _check_reply(response: httpx.Response) -> None:
    """Writes a warning when Arkesel's reply shows a problem. Never raises, never logs the URL or key."""
    try:
        data = response.json()
    except ValueError:
        log.warning("Arkesel sent a reply that is not JSON")
        return
    if not isinstance(data, dict):
        log.warning("Arkesel sent an unexpected reply")
        return

    code = str(data.get("code", ""))
    if code.lower() != "ok":
        log.warning("Arkesel did not accept the SMS (code=%s, message=%s)", code, str(data.get("message", ""))[:100])
        return

    balance = data.get("balance")
    if isinstance(balance, (int, float)) and not isinstance(balance, bool) and balance < LOW_BALANCE:
        log.warning("Arkesel SMS balance is low (%s credits left)", balance)


def send_sms(phone: str, message: str) -> None:
    """Sends one SMS through Arkesel. Raises httpx.HTTPError if the request fails."""
    # The API key travels in the query string, so this request must never be logged.
    response = httpx.get(
        ARKESEL_SMS_URL,
        params={
            "action": "send-sms",
            "api_key": settings.arkesel_api_key,
            "to": phone,
            "from": settings.arkesel_sender_id,
            "sms": message,
        },
        timeout=10,
    )
    response.raise_for_status()
    _check_reply(response)
