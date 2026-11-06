from tests.conftest import code_from

PHONE = "0244123456"
PASSWORD = "StrongPass123"


def register(client, phone=PHONE, password=PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ama Mensah", "phone": phone, "password": password},
    )


def verify(client, code, phone=PHONE):
    return client.post("/api/v1/auth/verify-phone", json={"phone": phone, "code": code})


def login(client, password=PASSWORD, phone=PHONE):
    return client.post("/api/v1/auth/login", json={"phone": phone, "password": password})


def test_register_sends_code_to_normalized_number(client, sms_outbox):
    assert register(client).status_code == 201
    assert sms_outbox[0][0] == "233244123456"


def test_login_refused_before_phone_verified(client, sms_outbox):
    register(client)
    assert login(client).status_code == 403


def test_correct_code_verifies_then_login_returns_token(client, sms_outbox):
    register(client)
    assert verify(client, code_from(sms_outbox)).status_code == 200
    response = login(client)
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_wrong_code_is_rejected(client, sms_outbox):
    register(client)
    real = code_from(sms_outbox)
    wrong = "111111" if real != "111111" else "222222"
    assert verify(client, wrong).status_code == 400


def test_code_cannot_be_reused(client, sms_outbox):
    register(client)
    code = code_from(sms_outbox)
    assert verify(client, code).status_code == 200
    assert verify(client, code).status_code == 400


def test_code_locks_after_five_wrong_attempts(client, sms_outbox):
    register(client)
    real = code_from(sms_outbox)
    wrong = "111111" if real != "111111" else "222222"
    for _ in range(5):
        assert verify(client, wrong).status_code == 400
    assert verify(client, real).status_code == 429


def test_account_locks_after_five_wrong_passwords(client, sms_outbox):
    register(client)
    verify(client, code_from(sms_outbox))
    for _ in range(5):
        assert login(client, password="wrong-password").status_code == 401
    assert login(client).status_code == 423


def test_resend_is_rate_limited(client, sms_outbox):
    register(client)
    assert client.post("/api/v1/auth/resend-code", json={"phone": PHONE}).status_code == 429


def test_duplicate_phone_rejected(client, sms_outbox):
    register(client)
    assert register(client).status_code == 409


def test_short_password_rejected(client, sms_outbox):
    assert register(client, password="short").status_code == 422


def test_invalid_phone_rejected(client, sms_outbox):
    assert register(client, phone="12345").status_code == 422
