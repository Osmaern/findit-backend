from app.models import User


def test_phone_is_unique_and_required():
    phone = User.__table__.c.phone
    assert phone.unique is True
    assert phone.nullable is False


def test_password_hash_is_required():
    assert User.__table__.c.password_hash.nullable is False


def test_email_is_optional():
    assert User.__table__.c.email.nullable is True
