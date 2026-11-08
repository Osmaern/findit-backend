import httpx
import pytest

from tests.test_items import FOUND, LOST, make_user

MESSAGE = {"message": "It has my name written inside the front pocket."}


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def claimant(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


@pytest.fixture
def third(client, sms_outbox):
    return make_user(client, sms_outbox, "0201234567")


def post_item(client, owner, payload=FOUND, **extra):
    return client.post("/api/v1/items", json={**payload, **extra}, headers=owner).json()["id"]


def claim(client, who, item_id, body=MESSAGE):
    return client.post(f"/api/v1/items/{item_id}/claims", json=body, headers=who)


def texts_to(outbox, phone):
    return [message for to, message in outbox if to == phone]


def test_anonymous_cannot_claim(client, owner):
    item_id = post_item(client, owner)
    client.cookies.clear()  # creating the user logged the test client in; this request must be anonymous
    assert client.post(f"/api/v1/items/{item_id}/claims", json=MESSAGE).status_code == 401


def test_claim_is_created_and_owner_is_texted(client, owner, claimant, sms_outbox):
    item_id = post_item(client, owner)
    response = claim(client, claimant, item_id)
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert any("claimed your item" in text for text in texts_to(sms_outbox, "233244123456"))


def test_claim_sms_never_contains_the_claim_message_or_phones(client, owner, claimant, sms_outbox):
    item_id = post_item(client, owner)
    claim(client, claimant, item_id)
    sms = " ".join(texts_to(sms_outbox, "233244123456"))
    assert MESSAGE["message"] not in sms
    assert "233551234567" not in sms


def test_cannot_claim_own_item(client, owner):
    item_id = post_item(client, owner)
    assert claim(client, owner, item_id).status_code == 403


def test_cannot_claim_twice(client, owner, claimant):
    item_id = post_item(client, owner)
    assert claim(client, claimant, item_id).status_code == 201
    assert claim(client, claimant, item_id).status_code == 409


def test_unknown_item_is_404(client, claimant):
    assert claim(client, claimant, 9999).status_code == 404


def test_short_message_rejected(client, owner, claimant):
    item_id = post_item(client, owner)
    assert claim(client, claimant, item_id, {"message": "mine"}).status_code == 422


def test_claimant_sees_own_claims_only(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim(client, claimant, item_id)
    assert len(client.get("/api/v1/claims/mine", headers=claimant).json()) == 1
    assert client.get("/api/v1/claims/mine", headers=third).json() == []


def test_owner_sees_received_claims_and_others_do_not(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim(client, claimant, item_id)
    received = client.get("/api/v1/claims/received", headers=owner).json()
    assert len(received) == 1
    assert received[0]["claimant_name"] == "Test User"
    assert received[0]["claimant_phone"] is None  # hidden until approval
    assert client.get("/api/v1/claims/received", headers=third).json() == []


def test_approve_updates_everything(client, owner, claimant, third, sms_outbox):
    item_id = post_item(client, owner)
    first = claim(client, claimant, item_id).json()["id"]
    second = claim(client, third, item_id).json()["id"]

    response = client.post(f"/api/v1/claims/{first}/approve", headers=owner)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["claimant_phone"] == "233551234567"

    assert client.get(f"/api/v1/items/{item_id}", headers=owner).json()["status"] == "claim_pending"
    losing = [c for c in client.get("/api/v1/claims/mine", headers=third).json() if c["id"] == second][0]
    assert losing["status"] == "declined"
    assert any("approved" in text for text in texts_to(sms_outbox, "233551234567"))
    assert any("not successful" in text for text in texts_to(sms_outbox, "233201234567"))


def test_item_leaves_the_public_list_after_approval(client, owner, claimant):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert client.get("/api/v1/items").json() == []


def test_owner_phone_shared_only_when_item_allows_contact(client, owner, claimant, third):
    open_item = post_item(client, owner, allow_contact=True)
    closed_item = post_item(client, owner, allow_contact=False)
    for item_id, who in ((open_item, claimant), (closed_item, third)):
        claim_id = claim(client, who, item_id).json()["id"]
        client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert client.get("/api/v1/claims/mine", headers=claimant).json()[0]["contact_phone"] == "233244123456"
    assert client.get("/api/v1/claims/mine", headers=third).json()[0]["contact_phone"] is None


def test_pending_claim_never_reveals_owner_phone(client, owner, claimant):
    item_id = post_item(client, owner, allow_contact=True)
    claim(client, claimant, item_id)
    assert client.get("/api/v1/claims/mine", headers=claimant).json()[0]["contact_phone"] is None


def test_only_the_owner_can_decide(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    assert client.post(f"/api/v1/claims/{claim_id}/approve", headers=third).status_code == 404
    assert client.post(f"/api/v1/claims/{claim_id}/approve", headers=claimant).status_code == 404
    assert client.post(f"/api/v1/claims/{claim_id}/decline", headers=third).status_code == 404


def test_decline_texts_the_claimant(client, owner, claimant, sms_outbox):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    response = client.post(f"/api/v1/claims/{claim_id}/decline", headers=owner)
    assert response.json()["status"] == "declined"
    assert any("not successful" in text for text in texts_to(sms_outbox, "233551234567"))
    assert client.get(f"/api/v1/items/{item_id}", headers=owner).json()["status"] == "open"


def test_a_decided_claim_cannot_be_decided_again(client, owner, claimant):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner).status_code == 409
    assert client.post(f"/api/v1/claims/{claim_id}/decline", headers=owner).status_code == 409


def test_cannot_claim_an_item_that_already_has_an_approved_claim(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert claim(client, third, item_id).status_code == 404


def test_claimant_can_withdraw_a_pending_claim(client, owner, claimant, third):
    item_id = post_item(client, owner)
    claim_id = claim(client, claimant, item_id).json()["id"]
    assert client.post(f"/api/v1/claims/{claim_id}/withdraw", headers=third).status_code == 404
    response = client.post(f"/api/v1/claims/{claim_id}/withdraw", headers=claimant)
    assert response.json()["status"] == "withdrawn"
    assert client.post(f"/api/v1/claims/{claim_id}/withdraw", headers=claimant).status_code == 409


def test_mark_returned_needs_an_approved_claim_and_the_owner(client, owner, claimant):
    item_id = post_item(client, owner)
    assert client.post(f"/api/v1/items/{item_id}/returned", headers=owner).status_code == 409
    claim_id = claim(client, claimant, item_id).json()["id"]
    client.post(f"/api/v1/claims/{claim_id}/approve", headers=owner)
    assert client.post(f"/api/v1/items/{item_id}/returned", headers=claimant).status_code == 404
    assert client.post(f"/api/v1/items/{item_id}/returned", headers=owner).status_code == 200
    assert client.get(f"/api/v1/items/{item_id}", headers=owner).json()["status"] == "returned"


def test_too_many_pending_claims_is_limited(client, owner, claimant, monkeypatch):
    monkeypatch.setattr("app.routers.claims.MAX_PENDING_PER_USER", 2)
    ids = [post_item(client, owner, LOST) for _ in range(3)]
    assert claim(client, claimant, ids[0]).status_code == 201
    assert claim(client, claimant, ids[1]).status_code == 201
    assert claim(client, claimant, ids[2]).status_code == 429


def test_a_failed_sms_does_not_break_the_claim(client, owner, claimant, monkeypatch):
    def broken(phone, message):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr("app.services.notify.send_sms", broken)
    item_id = post_item(client, owner)
    assert claim(client, claimant, item_id).status_code == 201


def test_item_reports_whether_the_viewer_is_the_owner(client, owner, claimant):
    item_id = post_item(client, owner)
    assert client.get(f"/api/v1/items/{item_id}", headers=owner).json()["is_owner"] is True
    assert client.get(f"/api/v1/items/{item_id}", headers=claimant).json()["is_owner"] is False
    assert client.get(f"/api/v1/items/{item_id}").json()["is_owner"] is False
