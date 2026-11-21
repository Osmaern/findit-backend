from datetime import timedelta

import pytest

from app.core.security import utc_now
from app.models.item import Item
from tests.conftest import TestingSession
from tests.test_claims import claim, post_item
from tests.test_items import FOUND, LOST, make_user


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def claimant(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


def test_stats_start_at_zero_and_need_no_login(client):
    response = client.get("/api/v1/items/stats")  # also proves "stats" is not mistaken for an item id
    assert response.status_code == 200
    assert response.json() == {"returned": 0, "open": 0}


def test_stats_count_open_items(client, owner):
    post_item(client, owner, FOUND)
    post_item(client, owner, LOST)
    assert client.get("/api/v1/items/stats").json() == {"returned": 0, "open": 2}


def test_stats_count_returned_items(client, owner, claimant):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    # Approved but not yet handed over: neither open nor returned.
    assert client.get("/api/v1/items/stats").json() == {"returned": 0, "open": 0}
    client.post(f"/api/v1/items/{item_id}/returned", headers=owner)
    assert client.get("/api/v1/items/stats").json() == {"returned": 1, "open": 0}


def test_stats_ignore_closed_and_expired_items(client, owner):
    closed = post_item(client, owner)
    client.post(f"/api/v1/items/{closed}/close", headers=owner)
    expired = post_item(client, owner)
    with TestingSession() as db:
        db.get(Item, expired).expires_at = utc_now() - timedelta(days=1)
        db.commit()
    assert client.get("/api/v1/items/stats").json() == {"returned": 0, "open": 0}


def test_stats_reveal_nothing_but_two_numbers(client, owner):
    post_item(client, owner)
    assert set(client.get("/api/v1/items/stats").json()) == {"returned", "open"}
