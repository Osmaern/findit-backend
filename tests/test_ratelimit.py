import pytest

from app.core import ratelimit
from app.core.config import settings

FORGOT = "/api/v1/auth/forgot-password"
BODY = {"phone": "0244123456"}


@pytest.fixture(autouse=True)
def limiter_on(monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", True)
    ratelimit.reset()


def hit(client, times, headers=None):
    return [client.post(FORGOT, json=BODY, headers=headers or {}).status_code for _ in range(times)]


def test_requests_over_the_limit_get_429_with_retry_after(client):
    assert hit(client, 10) == [200] * 10
    blocked = client.post(FORGOT, json=BODY)
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) > 0


def test_each_route_has_its_own_count(client):
    hit(client, 10)
    assert client.post("/api/v1/auth/resend-code", json=BODY).status_code == 200


def test_limit_applies_per_ip_when_the_proxy_is_trusted(client, monkeypatch):
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    hit(client, 10, {"X-Forwarded-For": "203.0.113.7"})
    assert client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": "203.0.113.7"}).status_code == 429
    assert client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": "203.0.113.8"}).status_code == 200


def test_the_proxy_header_cannot_be_used_to_dodge_the_limit_when_not_trusted(client):
    for index in range(10):
        client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": f"198.51.100.{index}"})
    assert client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": "198.51.100.99"}).status_code == 429


def test_a_client_cannot_dodge_the_limit_by_adding_its_own_forwarded_entry(client, monkeypatch):
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    # The proxy appends the real address last, so whatever the client put first is ignored
    for index in range(10):
        client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": f"198.51.100.{index}, 203.0.113.7"})
    blocked = client.post(FORGOT, json=BODY, headers={"X-Forwarded-For": "198.51.100.77, 203.0.113.7"})
    assert blocked.status_code == 429


def test_the_window_expires(client, monkeypatch):
    clock = [1000.0]
    monkeypatch.setattr(ratelimit, "_now", lambda: clock[0])
    hit(client, 10)
    assert client.post(FORGOT, json=BODY).status_code == 429
    clock[0] += 601
    assert client.post(FORGOT, json=BODY).status_code == 200


def test_switching_the_limiter_off_lets_everything_through(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_enabled", False)
    assert hit(client, 15) == [200] * 15


def test_idle_entries_are_pruned(monkeypatch):
    monkeypatch.setattr(ratelimit, "_PRUNE_ABOVE", 2)
    clock = [0.0]
    monkeypatch.setattr(ratelimit, "_now", lambda: clock[0])
    for index in range(3):
        ratelimit._hits[("x", f"ip{index}")].append(0.0)
    clock[0] = 4000.0

    class FakeRequest:
        headers: dict = {}
        client = type("C", (), {"host": "10.0.0.1"})()

    ratelimit.rate_limit("x", 5, 60)(FakeRequest())
    assert len(ratelimit._hits) == 1
