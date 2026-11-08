import logging

import httpx
import pytest

from app.core.config import settings
from app.services import sms

SECRET = "super-secret-key-123"


@pytest.fixture(autouse=True)
def fake_key(monkeypatch):
    monkeypatch.setattr(settings, "arkesel_api_key", SECRET)


def reply(monkeypatch, status=200, **kwargs):
    request = httpx.Request("GET", f"{sms.ARKESEL_SMS_URL}?api_key={SECRET}")
    monkeypatch.setattr(sms.httpx, "get", lambda *a, **k: httpx.Response(status, request=request, **kwargs))


def logged(caplog):
    return [r.getMessage() for r in caplog.records if r.name == "findit.sms"]


def test_a_healthy_reply_writes_nothing(monkeypatch, caplog):
    reply(monkeypatch, json={"code": "ok", "message": "Successfully Sent", "balance": 641})
    with caplog.at_level(logging.DEBUG):
        sms.send_sms("233244123456", "hello")
    assert logged(caplog) == []


def test_a_low_balance_is_warned_about(monkeypatch, caplog):
    reply(monkeypatch, json={"code": "ok", "message": "Successfully Sent", "balance": 3})
    with caplog.at_level(logging.WARNING):
        sms.send_sms("233244123456", "hello")
    assert logged(caplog) == ["Arkesel SMS balance is low (3 credits left)"]


def test_a_zero_balance_is_warned_about(monkeypatch, caplog):
    reply(monkeypatch, json={"code": "ok", "message": "Successfully Sent", "balance": 0})
    with caplog.at_level(logging.WARNING):
        sms.send_sms("233244123456", "hello")
    assert "low (0 credits left)" in logged(caplog)[0]


def test_a_rejected_sms_is_logged_with_the_reason_and_does_not_crash(monkeypatch, caplog):
    reply(monkeypatch, json={"code": "103", "message": "Invalid API key"})
    with caplog.at_level(logging.WARNING):
        sms.send_sms("233244123456", "hello")
    assert logged(caplog) == ["Arkesel did not accept the SMS (code=103, message=Invalid API key)"]


def test_a_reply_that_is_not_json_does_not_crash(monkeypatch, caplog):
    reply(monkeypatch, text="<html>Bad gateway page</html>")
    with caplog.at_level(logging.WARNING):
        sms.send_sms("233244123456", "hello")
    assert logged(caplog) == ["Arkesel sent a reply that is not JSON"]


def test_a_reply_that_is_not_an_object_does_not_crash(monkeypatch, caplog):
    reply(monkeypatch, json=["unexpected"])
    with caplog.at_level(logging.WARNING):
        sms.send_sms("233244123456", "hello")
    assert logged(caplog) == ["Arkesel sent an unexpected reply"]


def test_a_failed_request_still_raises_so_callers_can_handle_it(monkeypatch):
    reply(monkeypatch, status=502, text="down")
    with pytest.raises(httpx.HTTPStatusError):
        sms.send_sms("233244123456", "hello")


def test_the_api_key_never_reaches_the_logs(monkeypatch, caplog):
    for body in ({"code": "103", "message": "Invalid API key"}, {"code": "ok", "balance": 1}):
        reply(monkeypatch, json=body)
        with caplog.at_level(logging.DEBUG):
            sms.send_sms("233244123456", "hello")
    assert SECRET not in caplog.text
