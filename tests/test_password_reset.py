import re
from datetime import timedelta

import pytest

from app.core.security import utc_now
from app.models.otp import OTPCode
from tests.conftest import TestingSession
from tests.test_items import PASSWORD, make_user

PHONE = "0244123456"
NEW_PASSWORD = "BrandNewPass456"


@pytest.fixture
def account(client, sms_outbox):
    """A verified user. Returns the auth header they got when they logged in."""
    return make_user(client, sms_outbox, PHONE)


def reset_code(outbox) -> str:
    texts = [message for _, message in outbox if "reset code" in message]
    return re.search(r"code is (\d{6})", texts[-1]).group(1)


def ask_for_code(client, phone=PHONE):
    return client.post("/api/v1/auth/forgot-password", json={"phone": phone})


def reset(client, code, password=NEW_PASSWORD, phone=PHONE):
    return client.post("/api/v1/auth/reset-password", json={"phone": phone, "code": code, "new_password": password})


def login(client, password, phone=PHONE):
    return client.post("/api/v1/auth/login", json={"phone": phone, "password": password})


def test_registered_number_gets_a_reset_code(client, account, sms_outbox):
    assert ask_for_code(client).status_code == 200
    assert re.search(r"\d{6}", " ".join(m for _, m in sms_outbox if "reset code" in m))


def test_unknown_number_gets_the_same_answer_and_no_sms(client, sms_outbox):
    known = ask_for_code(client, "0501112223")
    assert known.status_code == 200
    assert not [m for _, m in sms_outbox if "reset code" in m]


def test_answer_is_identical_for_known_and_unknown_numbers(client, account):
    unknown = ask_for_code(client, "0501112223").json()
    known = ask_for_code(client).json()
    assert known == unknown


def test_unverified_account_gets_no_reset_code(client, sms_outbox):
    client.post("/api/v1/auth/register", json={"full_name": "New Person", "phone": "0551234567", "password": PASSWORD, "accept_terms": True})
    ask_for_code(client, "0551234567")
    assert not [m for _, m in sms_outbox if "reset code" in m]


def test_second_request_within_a_minute_is_ignored_quietly(client, account, sms_outbox):
    ask_for_code(client)
    response = ask_for_code(client)
    assert response.status_code == 200
    assert len([m for _, m in sms_outbox if "reset code" in m]) == 1


def test_correct_code_changes_the_password(client, account, sms_outbox):
    ask_for_code(client)
    response = reset(client, reset_code(sms_outbox))
    assert response.status_code == 200
    assert login(client, PASSWORD).status_code == 401
    assert login(client, NEW_PASSWORD).status_code == 200
    assert any("password was changed" in m for _, m in sms_outbox)


def test_reset_clears_an_account_lockout(client, account, sms_outbox):
    for _ in range(5):
        login(client, "wrong-password")
    assert login(client, NEW_PASSWORD).status_code == 423
    ask_for_code(client)
    reset(client, reset_code(sms_outbox))
    assert login(client, NEW_PASSWORD).status_code == 200


def test_wrong_code_is_rejected(client, account, sms_outbox):
    ask_for_code(client)
    assert reset(client, "000000" if reset_code(sms_outbox) != "000000" else "111111").status_code == 400
    assert login(client, PASSWORD).status_code == 200  # the old password still works


def test_code_cannot_be_used_twice(client, account, sms_outbox):
    ask_for_code(client)
    code = reset_code(sms_outbox)
    assert reset(client, code).status_code == 200
    assert reset(client, code, "AnotherPass789").status_code == 400


def test_too_many_wrong_guesses_lock_the_code(client, account, sms_outbox):
    ask_for_code(client)
    code = reset_code(sms_outbox)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(5):
        assert reset(client, wrong).status_code == 400
    assert reset(client, code).status_code == 429  # even the right code no longer works


def test_expired_code_is_rejected(client, account, sms_outbox):
    ask_for_code(client)
    with TestingSession() as db:
        for otp in db.query(OTPCode).filter(OTPCode.purpose == "reset"):
            otp.expires_at = utc_now() - timedelta(minutes=1)
        db.commit()
    assert reset(client, reset_code(sms_outbox)).status_code == 400


def test_a_newer_code_cancels_the_older_one(client, account, sms_outbox, monkeypatch):
    monkeypatch.setattr("app.routers.auth.OTP_RESEND_WAIT", timedelta(0))
    ask_for_code(client)
    first = reset_code(sms_outbox)
    ask_for_code(client)
    second = reset_code(sms_outbox)
    if first != second:  # (one in a million that they match)
        assert reset(client, first).status_code == 400
    assert reset(client, second).status_code == 200


def test_signup_code_cannot_reset_a_password(client, sms_outbox):
    client.post("/api/v1/auth/register", json={"full_name": "New Person", "phone": "0551234567", "password": PASSWORD, "accept_terms": True})
    signup_code = re.search(r"code is (\d{6})", sms_outbox[-1][1]).group(1)
    assert reset(client, signup_code, phone="0551234567").status_code == 400


def test_unknown_number_cannot_reset(client):
    assert reset(client, "123456", phone="0501112223").status_code == 400


def test_weak_new_password_is_rejected(client, account, sms_outbox):
    ask_for_code(client)
    assert reset(client, reset_code(sms_outbox), password="short").status_code == 422


def test_reset_signs_out_older_sessions(client, account, sms_outbox):
    assert client.get("/api/v1/auth/me", headers=account).status_code == 200
    ask_for_code(client)
    reset(client, reset_code(sms_outbox))
    assert client.get("/api/v1/auth/me", headers=account).status_code == 401
    fresh = login(client, NEW_PASSWORD).json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fresh}"}).status_code == 200
