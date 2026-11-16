from datetime import date, timedelta

import pytest

from app.core.security import utc_now
from app.models.item import Item
from app.services.matching import MAX_MATCHES, score, words
from tests.conftest import TestingSession
from tests.test_items import FOUND, LOST, TODAY, make_user


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def finder(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


def post(client, who, payload):
    return client.post("/api/v1/items", json=payload, headers=who).json()["id"]


def matches(client, item_id, headers=None):
    return client.get(f"/api/v1/items/{item_id}/matches", headers=headers or {})


PHONE_LOST = {**LOST, "title": "Samsung phone", "category": "phone", "location": "Library",
              "description": "Blue Samsung phone lost on the second floor of the library."}


def test_a_lost_report_matches_a_similar_found_report(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    found = post(client, finder, FOUND)  # Samsung phone, Library
    result = matches(client, lost)
    assert result.status_code == 200
    assert [item["id"] for item in result.json()] == [found]


def test_a_found_report_matches_a_similar_lost_report(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    found = post(client, finder, FOUND)
    assert [item["id"] for item in matches(client, found).json()] == [lost]


def test_unrelated_reports_do_not_match(client, owner, finder):
    lost = post(client, owner, LOST)  # black backpack, Main Hall
    post(client, finder, FOUND)  # Samsung phone, Library
    assert matches(client, lost).json() == []


def test_same_kind_reports_never_match(client, owner, finder):
    first = post(client, owner, PHONE_LOST)
    post(client, finder, {**PHONE_LOST, "title": "Samsung phone again"})
    assert matches(client, first).json() == []


def test_your_own_reports_are_not_suggested(client, owner):
    lost = post(client, owner, PHONE_LOST)
    post(client, owner, FOUND)
    assert matches(client, lost).json() == []


def test_closed_and_expired_reports_are_not_suggested(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    closed = post(client, finder, FOUND)
    expired = post(client, finder, FOUND)
    client.post(f"/api/v1/items/{closed}/close", headers=finder)
    with TestingSession() as db:
        db.get(Item, expired).expires_at = utc_now() - timedelta(days=1)
        db.commit()
    assert matches(client, lost).json() == []


def test_a_closed_report_has_no_matches_and_is_hidden_from_strangers(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    post(client, finder, FOUND)
    client.post(f"/api/v1/items/{lost}/close", headers=owner)
    assert matches(client, lost, owner).json() == []  # the owner may look, but nothing is suggested
    assert matches(client, lost, finder).status_code == 404


def test_unknown_item_is_404(client):
    assert client.get("/api/v1/items/9999/matches").status_code == 404


def test_matches_are_public_but_leak_no_private_data(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    post(client, finder, FOUND)
    client.cookies.clear()
    result = matches(client, lost)
    assert result.status_code == 200
    body = result.json()[0]
    assert body["private_detail"] is None
    assert body["is_owner"] is False
    assert "Cracked corner" not in result.text
    assert "233" not in result.text


def test_at_most_five_matches_best_first(client, owner, finder):
    lost = post(client, owner, PHONE_LOST)
    weak = post(client, finder, {**FOUND, "title": "Phone charger", "category": "electronics",
                                 "location": "Hostel", "description": "A white charger found at the hostel."})
    for number in range(MAX_MATCHES + 2):
        post(client, finder, {**FOUND, "title": f"Samsung phone {number}"})
    result = matches(client, lost).json()
    assert len(result) == MAX_MATCHES
    assert weak not in [item["id"] for item in result]


def test_words_ignores_short_and_filler_words():
    assert words("The BLACK bag, near a lecture hall!") == {"black", "bag", "lecture", "hall"}


def test_score_rewards_matching_title_category_place_and_date():
    def item(**values):
        base = dict(title="Black bag", description="A bag", category="bag", location="Library", event_date=date.today())
        return Item(**{**base, **values})

    same = score(item(), item())
    different_category = score(item(), item(category="other"))
    different_place = score(item(), item(location="Gate"))
    far_date = score(item(), item(event_date=date.today() - timedelta(days=60)))
    assert same > different_category and same > different_place and same > far_date
    assert score(item(), item(title="Umbrella", description="Red umbrella")) == 0
