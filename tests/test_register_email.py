from tests.conftest import code_from

PHONE = "0244123456"
PASSWORD = "StrongPass123"


def register(client, phone=PHONE, email="", password=PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        json={"full_name": "Ama Mensah", "phone": phone, "email": email, "password": password, "accept_terms": True},
    )


def test_register_accepts_optional_email(client, sms_outbox):
    assert register(client, email="Ama@Example.com").status_code == 201


def test_duplicate_email_rejected_case_insensitive(client, sms_outbox):
    register(client, email="ama@example.com")
    assert register(client, phone="0551234567", email="AMA@example.com").status_code == 409


def test_accounts_without_email_are_allowed(client, sms_outbox):
    assert register(client, phone="0244123456").status_code == 201
    assert register(client, phone="0551234567").status_code == 201


def test_invalid_email_rejected(client, sms_outbox):
    assert register(client, email="not-an-email").status_code == 422


def test_login_sets_http_only_cookie(client, sms_outbox):
    register(client)
    client.post("/api/v1/auth/verify-phone", json={"phone": PHONE, "code": code_from(sms_outbox)})
    response = client.post("/api/v1/auth/login", json={"phone": PHONE, "password": PASSWORD})
    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "httponly" in response.headers["set-cookie"].lower()
