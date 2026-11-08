from datetime import date
from io import BytesIO

import pytest
from PIL import Image

from tests.conftest import code_from

PASSWORD = "StrongPass123"
TODAY = date.today().isoformat()


def _tiny_png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, "PNG")
    return buffer.getvalue()


PNG = _tiny_png()
BAD_FILE = b"GIF89a" + b"0" * 64

LOST = {
    "kind": "lost",
    "title": "Black backpack",
    "category": "bag",
    "location": "Main Hall",
    "description": "Black backpack with a red zip, lost near the lecture hall.",
    "event_date": TODAY,
}
FOUND = {
    "kind": "found",
    "title": "Samsung phone",
    "category": "phone",
    "location": "Library",
    "description": "Blue phone found on the second floor of the library.",
    "event_date": TODAY,
    "private_detail": "Cracked corner, lock screen shows a lake",
}


def make_user(client, outbox, phone):
    client.post("/api/v1/auth/register", json={"full_name": "Test User", "phone": phone, "password": PASSWORD, "accept_terms": True})
    client.post("/api/v1/auth/verify-phone", json={"phone": phone, "code": code_from(outbox)})
    response = client.post("/api/v1/auth/login", json={"phone": phone, "password": PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def owner(client, sms_outbox):
    return make_user(client, sms_outbox, "0244123456")


@pytest.fixture
def other(client, sms_outbox):
    return make_user(client, sms_outbox, "0551234567")


@pytest.fixture
def photo_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.items.UPLOAD_DIR", tmp_path)
    return tmp_path


def test_anonymous_user_cannot_post(client):
    assert client.post("/api/v1/items", json=LOST).status_code == 401


def test_lost_item_is_created(client, owner):
    response = client.post("/api/v1/items", json=LOST, headers=owner)
    assert response.status_code == 201
    assert response.json()["private_detail"] is None


def test_found_item_requires_private_detail(client, owner):
    payload = {k: v for k, v in FOUND.items() if k != "private_detail"}
    assert client.post("/api/v1/items", json=payload, headers=owner).status_code == 422


def test_future_date_rejected(client, owner):
    payload = {**LOST, "event_date": "2999-01-01"}
    assert client.post("/api/v1/items", json=payload, headers=owner).status_code == 422


def test_private_detail_hidden_from_other_users(client, owner, other):
    client.post("/api/v1/items", json=FOUND, headers=owner)
    listing = client.get("/api/v1/items", headers=other)
    assert listing.status_code == 200
    assert "Cracked corner" not in listing.text
    item_id = listing.json()[0]["id"]
    detail = client.get(f"/api/v1/items/{item_id}", headers=other)
    assert detail.json()["private_detail"] is None


def test_private_detail_hidden_from_public_visitors(client, owner):
    client.post("/api/v1/items", json=FOUND, headers=owner)
    listing = client.get("/api/v1/items")
    assert "Cracked corner" not in listing.text


def test_owner_sees_private_detail(client, owner):
    created = client.post("/api/v1/items", json=FOUND, headers=owner).json()
    detail = client.get(f"/api/v1/items/{created['id']}", headers=owner)
    assert detail.json()["private_detail"] == FOUND["private_detail"]


def test_list_filters_by_kind(client, owner):
    client.post("/api/v1/items", json=LOST, headers=owner)
    client.post("/api/v1/items", json=FOUND, headers=owner)
    lost_only = client.get("/api/v1/items?kind=lost").json()
    assert len(lost_only) == 1
    assert lost_only[0]["kind"] == "lost"


def test_photo_png_accepted(client, owner, photo_dir):
    item_id = client.post("/api/v1/items", json=LOST, headers=owner).json()["id"]
    response = client.post(
        f"/api/v1/items/{item_id}/photos",
        files={"file": ("bag.png", PNG, "image/png")},
        headers=owner,
    )
    assert response.status_code == 201
    assert len(list(photo_dir.iterdir())) == 1


def test_fake_image_rejected(client, owner, photo_dir):
    item_id = client.post("/api/v1/items", json=LOST, headers=owner).json()["id"]
    response = client.post(
        f"/api/v1/items/{item_id}/photos",
        files={"file": ("bag.png", BAD_FILE, "image/png")},
        headers=owner,
    )
    assert response.status_code == 415


def test_third_photo_rejected(client, owner, photo_dir):
    item_id = client.post("/api/v1/items", json=LOST, headers=owner).json()["id"]
    for _ in range(2):
        client.post(f"/api/v1/items/{item_id}/photos", files={"file": ("a.png", PNG, "image/png")}, headers=owner)
    response = client.post(
        f"/api/v1/items/{item_id}/photos", files={"file": ("a.png", PNG, "image/png")}, headers=owner
    )
    assert response.status_code == 409


def test_other_user_cannot_add_photo(client, owner, other, photo_dir):
    item_id = client.post("/api/v1/items", json=LOST, headers=owner).json()["id"]
    response = client.post(
        f"/api/v1/items/{item_id}/photos", files={"file": ("a.png", PNG, "image/png")}, headers=other
    )
    assert response.status_code == 404
