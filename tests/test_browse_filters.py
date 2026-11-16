from datetime import timedelta

import pytest

from app.core.security import utc_now
from app.models.item import Item
from tests.conftest import TestingSession
from tests.test_items import FOUND, LOST, make_user


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


def post(client, owner, payload):
    return client.post("/api/v1/items", json=payload, headers=owner).json()["id"]


def titles(client, query):
    return sorted(item["title"] for item in client.get(f"/api/v1/items?{query}").json())


def test_location_filter_matches_part_of_the_name_in_any_case(client, owner):
    post(client, owner, LOST)  # Main Hall
    post(client, owner, FOUND)  # Library
    assert titles(client, "location=lib") == ["Samsung phone"]
    assert titles(client, "location=MAIN") == ["Black backpack"]
    assert titles(client, "location=hall") == ["Black backpack"]
    assert titles(client, "location=cafeteria") == []


def test_location_and_kind_filters_combine(client, owner):
    post(client, owner, LOST)
    post(client, owner, FOUND)
    assert titles(client, "kind=found&location=lib") == ["Samsung phone"]
    assert titles(client, "kind=lost&location=lib") == []


def test_search_treats_percent_and_underscore_as_plain_characters(client, owner):
    post(client, owner, LOST)
    assert titles(client, "q=%25") == []  # a lone % must not match everything
    assert titles(client, "q=_") == []
    assert titles(client, "q=BACKPACK") == ["Black backpack"]


def test_days_filter_keeps_only_recent_posts(client, owner):
    old_id = post(client, owner, LOST)
    post(client, owner, FOUND)
    with TestingSession() as db:
        db.get(Item, old_id).created_at = utc_now() - timedelta(days=10)
        db.commit()
    assert titles(client, "days=7") == ["Samsung phone"]
    assert titles(client, "days=30") == ["Black backpack", "Samsung phone"]
    assert titles(client, "") == ["Black backpack", "Samsung phone"]


def test_days_filter_rejects_nonsense(client):
    assert client.get("/api/v1/items?days=0").status_code == 422
    assert client.get("/api/v1/items?days=-3").status_code == 422
    assert client.get("/api/v1/items?days=1000").status_code == 422


def test_paging_with_offset_returns_the_next_items(client, owner):
    for number in range(3):
        post(client, owner, {**LOST, "title": f"Umbrella {number}"})
    first = client.get("/api/v1/items?limit=2").json()
    second = client.get("/api/v1/items?limit=2&offset=2").json()
    assert len(first) == 2 and len(second) == 1
    assert not {item["id"] for item in first} & {item["id"] for item in second}
