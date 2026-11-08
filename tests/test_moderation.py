import pytest

from app.models.user import User
from tests.conftest import TestingSession
from tests.test_claims import claim, post_item, texts_to
from tests.test_items import make_user


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def reporter(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


@pytest.fixture
def second_reporter(client, sms_outbox):
    return make_user(client, sms_outbox, "0201234567")


@pytest.fixture
def moderator(client, sms_outbox):
    headers = make_user(client, sms_outbox, "0261234567")
    set_role("233261234567", "moderator")
    return headers


def set_role(phone, role):
    with TestingSession() as db:
        db.query(User).filter(User.phone == phone).update({"role": role})
        db.commit()


def report(client, who, item_id, reason="spam", details=""):
    return client.post(f"/api/v1/items/{item_id}/report", json={"reason": reason, "details": details}, headers=who)


def test_reporting_needs_a_login(client, owner):
    item_id = post_item(client, owner)
    client.cookies.clear()
    assert client.post(f"/api/v1/items/{item_id}/report", json={"reason": "spam"}).status_code == 401


def test_a_member_can_report_a_post(client, owner, reporter):
    item_id = post_item(client, owner)
    assert report(client, reporter, item_id, "fake", "Looks made up").status_code == 201


def test_cannot_report_your_own_post(client, owner):
    assert report(client, owner, post_item(client, owner)).status_code == 403


def test_cannot_report_the_same_post_twice(client, owner, reporter):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    assert report(client, reporter, item_id).status_code == 409


def test_unknown_reason_is_rejected(client, owner, reporter):
    item_id = post_item(client, owner)
    assert report(client, reporter, item_id, "because").status_code == 422


def test_cannot_report_a_post_that_is_not_visible(client, owner, reporter):
    item_id = post_item(client, owner)
    client.post(f"/api/v1/items/{item_id}/close", headers=owner)
    assert report(client, reporter, item_id).status_code == 404
    assert report(client, reporter, 9999).status_code == 404


def test_members_cannot_use_the_admin_routes(client, owner, reporter):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    assert client.get("/api/v1/admin/reports", headers=reporter).status_code == 403
    assert client.post("/api/v1/admin/reports/1/remove", headers=reporter).status_code == 403
    assert client.post("/api/v1/admin/reports/1/dismiss", headers=reporter).status_code == 403
    assert client.post(f"/api/v1/admin/items/{item_id}/restore", headers=reporter).status_code == 403


def test_anonymous_cannot_use_the_admin_routes(client):
    assert client.get("/api/v1/admin/reports").status_code == 401


def test_moderator_sees_open_reports_with_the_number_waiting(client, owner, reporter, second_reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id, "spam")
    report(client, second_reporter, item_id, "fake", "Not real")
    reports = client.get("/api/v1/admin/reports", headers=moderator).json()
    assert len(reports) == 2
    assert reports[0]["open_reports_on_item"] == 2
    assert {entry["reason"] for entry in reports} == {"spam", "fake"}
    assert reports[0]["owner_name"] == "Test User"


def test_removing_a_post_hides_it_and_closes_every_report_on_it(client, owner, reporter, second_reporter, moderator):
    item_id = post_item(client, owner)
    first = report(client, reporter, item_id)
    report(client, second_reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]

    response = client.post(f"/api/v1/admin/reports/{report_id}/remove", headers=moderator)
    assert response.status_code == 200
    assert response.json()["item_status"] == "removed"
    assert first.status_code == 201
    assert client.get("/api/v1/items").json() == []
    assert client.get("/api/v1/admin/reports", headers=moderator).json() == []  # nothing left open
    assert client.get(f"/api/v1/items/{item_id}", headers=reporter).status_code == 404


def test_removing_texts_the_owner_and_declines_waiting_claims(client, owner, reporter, second_reporter, moderator, sms_outbox):
    item_id = post_item(client, owner)
    claim(client, second_reporter, item_id)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    client.post(f"/api/v1/admin/reports/{report_id}/remove", headers=moderator)

    assert any("removed by a moderator" in text for text in texts_to(sms_outbox, "233244123456"))
    assert any("removed by a moderator" in text for text in texts_to(sms_outbox, "233201234567"))
    assert client.get("/api/v1/claims/mine", headers=second_reporter).json()[0]["status"] == "declined"


def test_owner_still_sees_a_removed_post_marked_as_removed(client, owner, reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    client.post(f"/api/v1/admin/reports/{report_id}/remove", headers=moderator)
    assert client.get("/api/v1/items/mine", headers=owner).json()[0]["status"] == "removed"


def test_dismissing_keeps_the_post_up(client, owner, reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    response = client.post(f"/api/v1/admin/reports/{report_id}/dismiss", headers=moderator)
    assert response.json()["status"] == "dismissed"
    assert len(client.get("/api/v1/items").json()) == 1


def test_a_handled_report_cannot_be_handled_again(client, owner, reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    client.post(f"/api/v1/admin/reports/{report_id}/dismiss", headers=moderator)
    assert client.post(f"/api/v1/admin/reports/{report_id}/remove", headers=moderator).status_code == 409
    assert client.post(f"/api/v1/admin/reports/{report_id}/dismiss", headers=moderator).status_code == 409


def test_handled_filter_shows_actioned_and_dismissed(client, owner, reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    client.post(f"/api/v1/admin/reports/{report_id}/dismiss", headers=moderator)
    assert client.get("/api/v1/admin/reports?status=open", headers=moderator).json() == []
    assert len(client.get("/api/v1/admin/reports?status=handled", headers=moderator).json()) == 1
    assert len(client.get("/api/v1/admin/reports?status=all", headers=moderator).json()) == 1


def test_a_removed_post_can_be_restored(client, owner, reporter, moderator):
    item_id = post_item(client, owner)
    report(client, reporter, item_id)
    report_id = client.get("/api/v1/admin/reports", headers=moderator).json()[0]["id"]
    client.post(f"/api/v1/admin/reports/{report_id}/remove", headers=moderator)
    assert client.post(f"/api/v1/admin/items/{item_id}/restore", headers=moderator).status_code == 200
    assert len(client.get("/api/v1/items").json()) == 1
    assert client.post(f"/api/v1/admin/items/{item_id}/restore", headers=moderator).status_code == 409


def test_make_admin_script_changes_the_role(client, owner):
    from app.scripts.make_admin import set_role as script_set_role

    with TestingSession() as db:
        user = script_set_role(db, "0244123456", "admin")
        assert user.role == "admin"
        with pytest.raises(ValueError):
            script_set_role(db, "0244123456", "superuser")
        with pytest.raises(LookupError):
            script_set_role(db, "0501112223", "admin")
