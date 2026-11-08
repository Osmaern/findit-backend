import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (registers all tables)
from app.core import ratelimit
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app as fastapi_app

# Tests use an isolated in-memory database so they never touch your real data
test_engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=test_engine, autoflush=False)


def _override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def no_rate_limits(monkeypatch):
    """Tests make many requests from one address, so the limiter is off unless a test turns it on."""
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    ratelimit.reset()


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield


@pytest.fixture
def client():
    return TestClient(fastapi_app)


@pytest.fixture
def sms_outbox(monkeypatch):
    """Records SMS messages that the app would send; the real Arkesel call is replaced in tests only."""
    outbox = []
    record = lambda phone, message: outbox.append((phone, message))  # noqa: E731
    monkeypatch.setattr("app.routers.auth.send_sms", record)
    monkeypatch.setattr("app.services.notify.send_sms", record)
    return outbox


def code_from(outbox) -> str:
    _, message = outbox[-1]
    return re.search(r"code is (\d{6})", message).group(1)
