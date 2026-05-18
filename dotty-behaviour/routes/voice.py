"""Voice-tool helper routes — small read-only endpoints invoked by
dotty-pi-ext's TypeScript tool implementations.

Today only `take_photo` lives here. The other four pi-ext tools
(memory_lookup, remember, think_hard, play_song) talk directly to
brain.db or xiaozhi-server and don't need a dotty-behaviour endpoint.
"""

from __future__ import annotations

import logging
from time import perf_counter

from fastapi import APIRouter, Depends, Request

from perception import PerceptionState

log = logging.getLogger("dotty-behaviour.routes.voice")


def get_perception_state(request: Request) -> PerceptionState:
    state = getattr(request.app.state, "perception", None)
    if state is None:
        raise RuntimeError("PerceptionState not attached to app.state")
    return state


TAKE_PHOTO_FRESHNESS_SEC = 30.0
TAKE_PHOTO_FALLBACK = "(I can't see anything fresh right now)"
TAKE_PHOTO_MAX_CHARS = 300


router = APIRouter()


@router.get("/api/voice/take_photo")
async def voice_take_photo(
    state: PerceptionState = Depends(get_perception_state),
) -> dict:
    """Return the latest cached vision description if ≤30 s old.

    Wire-compatible with bridge.py's `_voice_tool_take_photo` v1
    behaviour: picks the freshest entry across all devices, returns the
    description capped at 300 chars, falls back to a fixed string when
    nothing is fresh. Future v2: actively fire take_photo MCP and await
    a new capture.
    """
    best_desc = ""
    best_age = float("inf")
    now = perf_counter()
    for entry in state.vision_cache.values():
        age = now - entry.get("timestamp", 0.0)
        if age < best_age and entry.get("description"):
            best_age = age
            best_desc = entry.get("description", "")
    if best_desc and best_age <= TAKE_PHOTO_FRESHNESS_SEC:
        return {"description": best_desc[:TAKE_PHOTO_MAX_CHARS]}
    return {"description": TAKE_PHOTO_FALLBACK}
