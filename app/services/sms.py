import httpx

from app.core.config import settings

ARKESEL_SMS_URL = "https://sms.arkesel.com/sms/api"


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
