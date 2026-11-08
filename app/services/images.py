from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SIDE = 2000  # longest edge, in pixels, after cleaning
MAX_PIXELS = 40_000_000  # refuse enormous images that would eat memory when decoded


class InvalidImage(ValueError):
    """The bytes look like an image but cannot be decoded safely."""


def clean_image(data: bytes, content_type: str) -> bytes:
    """Re-encodes a photo so it carries no hidden data.

    Phone photos record the GPS position, the time and the camera model. Anyone who downloads the picture
    could read where the item (and so probably the owner) was. Re-saving the pixels only drops all of that.
    The camera's rotation is applied first so the picture still looks the right way up.
    """
    try:
        with Image.open(BytesIO(data)) as opened:
            if opened.width * opened.height > MAX_PIXELS:
                raise InvalidImage("Image is too large")
            opened.load()  # decode everything now, so a corrupt file fails here and not later
            image = ImageOps.exif_transpose(opened)
            image.thumbnail((MAX_SIDE, MAX_SIDE))

            out = BytesIO()
            if content_type == "image/jpeg":
                image.convert("RGB").save(out, "JPEG", quality=85, optimize=True)
            elif content_type == "image/png":
                image.save(out, "PNG", optimize=True)
            else:
                image.save(out, "WEBP", quality=85)
            return out.getvalue()
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError) as exc:
        raise InvalidImage("Not a valid image") from exc
