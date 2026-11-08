from datetime import timedelta

import pytest

from app.core.security import utc_now
from app.models.item import Item
from tests.conftest import TestingSession
from tests.test_claims import MESSAGE, claim, post_item, texts_to
from tests.test_items import FOUND, LOST, make_user


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def claimant(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


@pytest.fixture
def third(client, sms_outbox):
    return make_user(client, sms_outbox, "0201234567")


def test_my_posts_requires_login(client, owner):
    client.cookies.clear()
    assert client.get("/api/v1/items/mine").status_code == 401


def test_my_posts_lists_only_my_items_with_private_detail(client, owner, claimant):
    post_item(client, owner, FOUND)
    post_item(client, claimant, LOST)
    mine = client.get("/api/v1/items/mine", headers=owner)
    assert mine.status_code == 200  # "mine" must not be mistaken for an item id
    assert [item["kind"] for item in mine.json()] == ["found"]
    assert mine.json()[0]["private_detail"] == FOUND["private_detail"]


def test_my_posts_counts_waiting_claims(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim(client, claimant, item_id)
    claim(client, third, item_id)
    assert client.get("/api/v1/items/mine", headers=owner).json()[0]["pending_claims"] == 2


def test_my_posts_shows_closed_returned_and_expired_items(client, owner, claimant):
    closed = post_item(client, owner)
    client.post(f"/api/v1/items/{closed}/close", headers=owner)
    expired = post_item(client, owner)
    with TestingSession() as db:
        db.get(Item, expired).expires_at = utc_now() - timedelta(days=1)
        db.commit()
    statuses = {item["id"]: item["status"] for item in client.get("/api/v1/items/mine", headers=owner).json()}
    assert statuses[closed] == "closed"
    assert statuses[expired] == "expired"


def test_close_hides_the_item_from_the_public_list(client, owner):
    item_id = post_item(client, owner)
    response = client.post(f"/api/v1/items/{item_id}/close", headers=owner)
    assert response.status_code == 200
    assert response.json()["status"] == "closed"
    assert client.get("/api/v1/items").json() == []


def test_close_declines_waiting_claims_and_texts_claimants(client, owner, claimant, sms_outbox):
    item_id = post_item(client, owner)
    claim(client, claimant, item_id)
    client.post(f"/api/v1/items/{item_id}/close", headers=owner)
    assert client.get("/api/v1/claims/mine", headers=claimant).json()[0]["status"] == "declined"
    assert any("closed by its owner" in text for text in texts_to(sms_outbox, "233551234567"))


def test_only_the_owner_can_close(client, owner, claimant):
    item_id = post_item(client, owner)
    assert client.post(f"/api/v1/items/{item_id}/close", headers=claimant).status_code == 404
    assert client.get(f"/api/v1/items/{item_id}", headers=owner).json()["status"] == "open"


def test_cannot_close_twice_or_after_approval(client, owner, claimant):
    first = post_item(client, owner)
    client.post(f"/api/v1/items/{first}/close", headers=owner)
    assert client.post(f"/api/v1/items/{first}/close", headers=owner).status_code == 409

    second = post_item(client, owner)
    claim_id = claim(client, claimant, second).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert client.post(f"/api/v1/items/{second}/close", headers=owner).status_code == 409


def test_cannot_claim_a_closed_item(client, owner, claimant):
    item_id = post_item(client, owner)
    client.post(f"/api/v1/items/{item_id}/close", headers=owner)
    assert claim(client, claimant, item_id, MESSAGE).status_code == 404
