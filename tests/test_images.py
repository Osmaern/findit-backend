from io import BytesIO

import pytest
from PIL import Image

from app.services.images import InvalidImage, clean_image
from tests.test_items import FOUND, make_user

GPS_IFD = 0x8825
ORIENTATION = 0x0112


def jpeg_with_gps(size=(40, 20), orientation=None) -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "SecretCameraMaker"
    gps = exif.get_ifd(GPS_IFD)
    gps[1], gps[2], gps[3], gps[4] = "N", (5.6, 0.2, 0.0), "W", (0.2, 0.1, 0.0)
    if orientation:
        exif[ORIENTATION] = orientation
    buffer = BytesIO()
    Image.new("RGB", size, "red").save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


def test_the_test_photo_really_has_a_gps_position():
    assert Image.open(BytesIO(jpeg_with_gps())).getexif().get_ifd(GPS_IFD)


def test_gps_and_camera_details_are_removed_from_jpeg():
    cleaned = clean_image(jpeg_with_gps(), "image/jpeg")
    exif = Image.open(BytesIO(cleaned)).getexif()
    assert not exif.get_ifd(GPS_IFD)
    assert len(exif) == 0
    assert b"SecretCameraMaker" not in cleaned
    assert b"Exif" not in cleaned


def test_rotation_is_applied_before_the_details_are_dropped():
    cleaned = clean_image(jpeg_with_gps(size=(40, 20), orientation=6), "image/jpeg")
    assert Image.open(BytesIO(cleaned)).size == (20, 40)


def test_png_text_chunks_are_removed():
    from PIL.PngImagePlugin import PngInfo

    info = PngInfo()
    info.add_text("Location", "SecretPlace")
    buffer = BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, "PNG", pnginfo=info)
    assert b"SecretPlace" in buffer.getvalue()
    assert b"SecretPlace" not in clean_image(buffer.getvalue(), "image/png")


def test_webp_is_cleaned_and_still_a_webp():
    buffer = BytesIO()
    Image.new("RGB", (8, 8)).save(buffer, "WEBP")
    assert Image.open(BytesIO(clean_image(buffer.getvalue(), "image/webp"))).format == "WEBP"


def test_big_pictures_are_shrunk():
    buffer = BytesIO()
    Image.new("RGB", (3000, 1000)).save(buffer, "PNG")
    cleaned = Image.open(BytesIO(clean_image(buffer.getvalue(), "image/png")))
    assert max(cleaned.size) == 2000


def test_a_corrupt_image_is_rejected():
    with pytest.raises(InvalidImage):
        clean_image(b"\xff\xd8\xff" + b"not really a picture" * 10, "image/jpeg")


@pytest.fixture
def photo_dir(tmp_path, monkeypatch):
    monkeypatch.setattr("app.routers.items.UPLOAD_DIR", tmp_path)
    return tmp_path


def test_uploaded_photo_is_stored_without_gps(client, sms_outbox, photo_dir):
    owner = make_user(client, sms_outbox, "0244123456")
    item_id = client.post("/api/v1/items", json=FOUND, headers=owner).json()["id"]
    response = client.post(
        f"/api/v1/items/{item_id}/photos",
        files={"file": ("phone.jpg", jpeg_with_gps(), "image/jpeg")},
        headers=owner,
    )
    assert response.status_code == 201
    stored = next(photo_dir.iterdir())
    assert not Image.open(stored).getexif().get_ifd(GPS_IFD)
    assert b"SecretCameraMaker" not in stored.read_bytes()


def test_corrupt_upload_is_refused(client, sms_outbox, photo_dir):
    owner = make_user(client, sms_outbox, "0244123456")
    item_id = client.post("/api/v1/items", json=FOUND, headers=owner).json()["id"]
    response = client.post(
        f"/api/v1/items/{item_id}/photos",
        files={"file": ("bad.jpg", b"\xff\xd8\xff" + b"junk" * 50, "image/jpeg")},
        headers=owner,
    )
    assert response.status_code == 415
    assert list(photo_dir.iterdir()) == []
