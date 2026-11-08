from tests.test_items import make_user


def test_me_requires_login(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(client, sms_outbox):
    headers = make_user(client, sms_outbox, "0244123456")
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["phone"] == "233244123456"


def test_logout_clears_cookie(client, sms_outbox):
    make_user(client, sms_outbox, "0244123456")
    response = client.post("/api/v1/auth/logout", json={})
    assert response.status_code == 200
    assert "max-age=0" in response.headers["set-cookie"].lower()
