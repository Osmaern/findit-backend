import pytest

from app.models.user import User
from tests.conftest import TestingSession
from tests.test_claims import claim, post_item, texts_to
from tests.test_items import PASSWORD, make_user
from tests.test_moderation import set_role


def user_id(phone):
    with TestingSession() as db:
        return db.query(User).filter(User.phone == phone).one().id


@pytest.fixture
def admin(client, sms_outbox):
    headers = make_user(client, sms_outbox, "0271234567")
    set_role("233271234567", "admin")
    return headers


@pytest.fixture
def moderator(client, sms_outbox):
    headers = make_user(client, sms_outbox, "0261234567")
    set_role("233261234567", "moderator")
    return headers


@pytest.fixture
def member(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def other(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


ADMIN_ROUTES = [
    ("get", "/api/v1/admin/stats"),
    ("get", "/api/v1/admin/users"),
    ("post", "/api/v1/admin/users/1/suspend"),
    ("post", "/api/v1/admin/users/1/restore"),
]


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_anonymous_is_turned_away(client, method, path):
    assert getattr(client, method)(path).status_code == 401


@pytest.mark.parametrize("method,path", ADMIN_ROUTES)
def test_members_and_moderators_cannot_use_admin_user_tools(client, member, moderator, method, path):
    assert getattr(client, method)(path, headers=member).status_code == 403
    assert getattr(client, method)(path, headers=moderator).status_code == 403


def test_totals_count_what_exists(client, admin, member, other):
    item_id = post_item(client, member)
    claim(client, other, item_id)
    stats = client.get("/api/v1/admin/stats", headers=admin).json()
    assert stats["users"] == {"total": 3, "verified": 3, "suspended": 0, "staff": 1}
    assert stats["items"]["open_found"] == 1
    assert stats["items"]["open_lost"] == 0
    assert stats["claims"]["pending"] == 1
    assert stats["open_reports"] == 0


def test_list_shows_users_without_secrets(client, admin, member):
    rows = client.get("/api/v1/admin/users", headers=admin).json()
    assert {row["phone"] for row in rows} == {"233271234567", "233244123456"}
    assert all("password_hash" not in row and "token_version" not in row for row in rows)


def test_search_by_name(client, admin, member, other):
    assert len(client.get("/api/v1/admin/users?q=Test", headers=admin).json()) == 3
    assert client.get("/api/v1/admin/users?q=Nobody", headers=admin).json() == []


def test_search_by_phone_typed_the_way_people_write_it(client, admin, member, other):
    rows = client.get("/api/v1/admin/users?q=0551234567", headers=admin).json()
    assert [row["phone"] for row in rows] == ["233551234567"]


def test_search_by_local_phone_format_finds_the_user(client, admin, member):
    rows = client.get("/api/v1/admin/users?q=244123456", headers=admin).json()
    assert [row["phone"] for row in rows] == ["233244123456"]


def test_suspending_blocks_login_and_current_session(client, admin, member, sms_outbox):
    target = user_id("233244123456")
    response = client.post(f"/api/v1/admin/users/{target}/suspend", headers=admin)
    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert client.get("/api/v1/auth/me", headers=member).status_code == 401
    login = client.post("/api/v1/auth/login", json={"phone": "0244123456", "password": PASSWORD})
    assert login.status_code == 403
    assert "suspended" in login.json()["detail"]
    assert any("suspended" in text for text in texts_to(sms_outbox, "233244123456"))


def test_a_wrong_password_does_not_reveal_that_an_account_is_suspended(client, admin, member):
    client.post(f"/api/v1/admin/users/{user_id('233244123456')}/suspend", headers=admin)
    login = client.post("/api/v1/auth/login", json={"phone": "0244123456", "password": "WrongPass999"})
    assert login.status_code == 401


def test_suspended_filter_lists_only_suspended_people(client, admin, member, other):
    client.post(f"/api/v1/admin/users/{user_id('233244123456')}/suspend", headers=admin)
    rows = client.get("/api/v1/admin/users?status=suspended", headers=admin).json()
    assert [row["phone"] for row in rows] == ["233244123456"]
    assert client.get("/api/v1/admin/stats", headers=admin).json()["users"]["suspended"] == 1


def test_cannot_suspend_yourself(client, admin):
    assert client.post(f"/api/v1/admin/users/{user_id('233271234567')}/suspend", headers=admin).status_code == 400


def test_cannot_suspend_another_admin(client, admin, sms_outbox):
    make_user(client, sms_outbox, "0501234567")
    set_role("233501234567", "admin")
    assert client.post(f"/api/v1/admin/users/{user_id('233501234567')}/suspend", headers=admin).status_code == 403


def test_unknown_user_is_404(client, admin):
    assert client.post("/api/v1/admin/users/9999/suspend", headers=admin).status_code == 404
    assert client.post("/api/v1/admin/users/9999/restore", headers=admin).status_code == 404


def test_suspending_twice_and_restoring_an_active_user_are_refused(client, admin, member):
    target = user_id("233244123456")
    assert client.post(f"/api/v1/admin/users/{target}/restore", headers=admin).status_code == 409
    client.post(f"/api/v1/admin/users/{target}/suspend", headers=admin)
    assert client.post(f"/api/v1/admin/users/{target}/suspend", headers=admin).status_code == 409


def test_restoring_lets_the_person_log_in_but_old_sessions_stay_dead(client, admin, member, sms_outbox):
    target = user_id("233244123456")
    client.post(f"/api/v1/admin/users/{target}/suspend", headers=admin)
    response = client.post(f"/api/v1/admin/users/{target}/restore", headers=admin)
    assert response.status_code == 200 and response.json()["is_active"] is True
    assert client.get("/api/v1/auth/me", headers=member).status_code == 401  # the old token is still dead
    login = client.post("/api/v1/auth/login", json={"phone": "0244123456", "password": PASSWORD})
    assert login.status_code == 200
    assert any("restored" in text for text in texts_to(sms_outbox, "233244123456"))
