import pytest

from tests.test_items import PASSWORD, make_user


@pytest.fixture
def me(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


def test_profile_needs_a_login(client):
    client.cookies.clear()
    assert client.get("/api/v1/profile").status_code == 401


def test_profile_shows_details_and_never_the_password(client, me):
    body = client.get("/api/v1/profile", headers=me).json()
    assert body["phone"] == "233244123456"
    assert body["full_name"] == "Test User"
    assert "password" not in str(body).lower()


def test_name_and_email_can_be_changed(client, me):
    response = client.put("/api/v1/profile", json={"full_name": "  Kofi   Mensah ", "email": " Kofi@Example.com "}, headers=me)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Kofi Mensah"
    assert response.json()["email"] == "kofi@example.com"


def test_email_can_be_removed(client, me):
    client.put("/api/v1/profile", json={"full_name": "Kofi Mensah", "email": "kofi@example.com"}, headers=me)
    response = client.put("/api/v1/profile", json={"full_name": "Kofi Mensah", "email": ""}, headers=me)
    assert response.json()["email"] is None


def test_bad_email_is_rejected(client, me):
    response = client.put("/api/v1/profile", json={"full_name": "Kofi Mensah", "email": "not-an-email"}, headers=me)
    assert response.status_code == 422


def test_name_must_have_letters(client, me):
    assert client.put("/api/v1/profile", json={"full_name": "  "}, headers=me).status_code == 422


def test_email_used_by_someone_else_is_refused(client, me, sms_outbox):
    other = make_user(client, sms_outbox, "0551234567")
    client.put("/api/v1/profile", json={"full_name": "Ama Owusu", "email": "shared@example.com"}, headers=other)
    response = client.put("/api/v1/profile", json={"full_name": "Kofi Mensah", "email": "shared@example.com"}, headers=me)
    assert response.status_code == 409


def test_phone_cannot_be_changed_here(client, me):
    client.put("/api/v1/profile", json={"full_name": "Kofi Mensah", "phone": "0500000000"}, headers=me)
    assert client.get("/api/v1/profile", headers=me).json()["phone"] == "233244123456"


def test_password_change_needs_the_current_password(client, me):
    response = client.post("/api/v1/profile/password", json={"current_password": "wrong", "new_password": "NewPass4567"}, headers=me)
    assert response.status_code == 400


def test_new_password_must_differ_and_be_long_enough(client, me):
    assert client.post("/api/v1/profile/password", json={"current_password": PASSWORD, "new_password": PASSWORD}, headers=me).status_code == 400
    assert client.post("/api/v1/profile/password", json={"current_password": PASSWORD, "new_password": "short"}, headers=me).status_code == 422


def test_password_change_works_and_old_password_stops(client, me, sms_outbox):
    response = client.post("/api/v1/profile/password", json={"current_password": PASSWORD, "new_password": "NewPass4567"}, headers=me)
    assert response.status_code == 200
    assert client.post("/api/v1/auth/login", json={"phone": "0244123456", "password": PASSWORD}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"phone": "0244123456", "password": "NewPass4567"}).status_code == 200
    assert any("password was changed" in text for _, text in sms_outbox)


def test_password_change_keeps_this_browser_signed_in(client, me):
    client.post("/api/v1/profile/password", json={"current_password": PASSWORD, "new_password": "NewPass4567"}, headers=me)
    assert client.get("/api/v1/profile", headers=me).status_code == 401  # the old token is gone
    assert client.get("/api/v1/profile").status_code == 200  # the cookie set by the change works
