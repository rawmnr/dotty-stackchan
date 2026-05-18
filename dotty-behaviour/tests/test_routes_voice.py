"""voice/take_photo route tests."""

from __future__ import annotations

from time import perf_counter

from fastapi.testclient import TestClient

from main import app
from routes.voice import TAKE_PHOTO_FALLBACK


def test_take_photo_returns_fallback_when_cache_empty() -> None:
    with TestClient(app) as client:
        state = client.app.state.perception
        state.vision_cache.clear()
        r = client.get("/api/voice/take_photo")
        assert r.status_code == 200
        assert r.json() == {"description": TAKE_PHOTO_FALLBACK}


def test_take_photo_returns_fresh_description() -> None:
    with TestClient(app) as client:
        state = client.app.state.perception
        state.vision_cache.clear()
        state.vision_cache["dev-1"] = {
            "description": "A blue chair and a wooden table.",
            "timestamp": perf_counter(),
        }
        r = client.get("/api/voice/take_photo")
        assert r.status_code == 200
        assert r.json() == {"description": "A blue chair and a wooden table."}


def test_take_photo_caps_description_at_300_chars() -> None:
    with TestClient(app) as client:
        state = client.app.state.perception
        state.vision_cache.clear()
        long = "A " + ("very long description " * 50)
        state.vision_cache["dev-1"] = {
            "description": long,
            "timestamp": perf_counter(),
        }
        r = client.get("/api/voice/take_photo")
        assert len(r.json()["description"]) == 300


def test_take_photo_picks_freshest_across_devices() -> None:
    with TestClient(app) as client:
        state = client.app.state.perception
        state.vision_cache.clear()
        now = perf_counter()
        state.vision_cache["dev-old"] = {
            "description": "Old description.",
            "timestamp": now - 10.0,
        }
        state.vision_cache["dev-new"] = {
            "description": "Fresh description.",
            "timestamp": now,
        }
        r = client.get("/api/voice/take_photo")
        assert r.json() == {"description": "Fresh description."}


def test_take_photo_returns_fallback_when_stale() -> None:
    with TestClient(app) as client:
        state = client.app.state.perception
        state.vision_cache.clear()
        state.vision_cache["dev-1"] = {
            "description": "Stale description.",
            "timestamp": perf_counter() - 999.0,
        }
        r = client.get("/api/voice/take_photo")
        assert r.json() == {"description": TAKE_PHOTO_FALLBACK}
