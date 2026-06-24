from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


def env_true(value: str | None) -> bool:
    return str(value or "").lower() in ("1", "true", "yes", "on")


def safe_component(value: object) -> str:
    text = str(value or "sessionless").strip()
    safe = "".join(
        ch if ch.isalnum() or ch in ("-", "_", ".") else "_"
        for ch in text
    )
    return safe or "sessionless"


def make_turn_id(session_id: object, stage: str, seq: int) -> str:
    return f"{safe_component(session_id)}-{stage}-{seq}"


def elapsed_ms(start: float, *, clock: Callable[[], float] = time.perf_counter) -> int:
    return int(round((clock() - start) * 1000))


@dataclass
class TurnSummary:
    turn_id: str
    duration_ms: int
    segments: int
    chars: int


class StreamingTurnTracker:
    def __init__(
        self,
        stage: str,
        *,
        clock: Callable[[], float] = time.perf_counter,
    ):
        self._stage = stage
        self._clock = clock
        self._seq = 0
        self._active_turn_id: str | None = None
        self._start: float | None = None
        self._segments = 0
        self._chars = 0

    def begin(self, session_id: object) -> str:
        self._seq += 1
        self._active_turn_id = make_turn_id(session_id, self._stage, self._seq)
        self._start = self._clock()
        self._segments = 0
        self._chars = 0
        return self._active_turn_id

    def current_turn_id(self) -> str | None:
        return self._active_turn_id

    def note_segment(self, text: str) -> None:
        if self._active_turn_id is None:
            return
        self._segments += 1
        self._chars += len(text or "")

    def finish(self) -> TurnSummary | None:
        if self._active_turn_id is None or self._start is None:
            return None
        summary = TurnSummary(
            turn_id=self._active_turn_id,
            duration_ms=elapsed_ms(self._start, clock=self._clock),
            segments=self._segments,
            chars=self._chars,
        )
        self._active_turn_id = None
        self._start = None
        self._segments = 0
        self._chars = 0
        return summary
