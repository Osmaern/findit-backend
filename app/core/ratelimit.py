"""A simple per-IP rate limiter for the endpoints people could abuse (login, sign-up, SMS-sending routes).

It keeps the recent request times in this process's memory. That is enough for one server. When the app runs
as several processes or servers, each has its own counts, so move the counts to a shared store such as Redis.

Limits are per IP address and deliberately generous: many students share one campus Wi-Fi address.
The strict protections are per account (login lockout, one SMS code per minute).
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.core.config import settings

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_PRUNE_ABOVE = 10_000  # once this many (route, IP) pairs are tracked, forget the idle ones


def _now() -> float:
    return time.monotonic()


def reset() -> None:
    """Forgets all counts. Used by the tests."""
    with _lock:
        _hits.clear()


def client_ip(request: Request) -> str:
    if settings.trust_proxy_headers:
        # Behind our own reverse proxy the last entry is the address the proxy saw. Earlier entries
        # are whatever the client sent, so they cannot be trusted.
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "unknown"


def _prune(now: float, longest_window: float) -> None:
    for key in [key for key, hits in _hits.items() if not hits or now - hits[-1] > longest_window]:
        del _hits[key]


def rate_limit(name: str, limit: int, per_seconds: int):
    """Dependency: allows `limit` requests per `per_seconds` for each IP, then answers 429."""

    def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        key = (name, client_ip(request))
        now = _now()
        with _lock:
            if len(_hits) > _PRUNE_ABOVE:
                _prune(now, longest_window=3600)
            hits = _hits[key]
            while hits and now - hits[0] > per_seconds:
                hits.popleft()
            if len(hits) >= limit:
                retry_after = int(per_seconds - (now - hits[0])) + 1
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please wait a little and try again.",
                    headers={"Retry-After": str(retry_after)},
                )
            hits.append(now)

    return dependency
