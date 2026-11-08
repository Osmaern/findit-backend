from app.models.user import User
from tests.conftest import TestingSession
from tests.test_items import PASSWORD

PERSON = {"full_name": "Ama Mensah", "phone": "0244123456", "password": PASSWORD}


def register(client, **extra):
    return client.post("/api/v1/auth/register", json={**PERSON, **extra})


def test_registration_needs_the_terms_to_be_accepted(client, sms_outbox):
    response = register(client)  # the field is missing
    assert response.status_code == 422
    assert "Terms and Privacy Policy" in response.json()["detail"][0]["msg"]
    assert sms_outbox == []


def test_ticking_no_is_refused_too(client, sms_outbox):
    assert register(client, accept_terms=False).status_code == 422
    assert sms_outbox == []


def test_only_a_real_yes_counts(client, sms_outbox):
    for sneaky in ("yes", "true", 1, "on"):
        assert register(client, accept_terms=sneaky).status_code == 422, sneaky


def test_nobody_is_created_when_the_terms_are_not_accepted(client, sms_outbox):
    register(client)
    with TestingSession() as db:
        assert db.query(User).count() == 0


def test_the_time_of_acceptance_is_saved(client, sms_outbox):
    assert register(client, accept_terms=True).status_code == 201
    with TestingSession() as db:
        user = db.query(User).one()
        assert user.terms_accepted_at is not None
