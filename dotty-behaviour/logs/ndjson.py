"""Daily-rotated, append-only NDJSON writer.

Lifted from bridge.py's `_write_jsonl_record` + the per-kind path
helpers (`_dreams_log_path`, `_dances_log_path`, etc.) into a small
class so consumers can own a writer instance instead of importing
top-level functions.

Behaviour matches bridge.py:
  * `ensure_ascii=False` so unicode in narrative text round-trips
  * mode 0600 set after each append (best-effort)
  * parents created on demand
  * any IOError is logged and swallowed — perception loops must not
    crash on a failed disk write
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

log = logging.getLogger("dotty-behaviour.logs.ndjson")


class NdjsonWriter:
    def __init__(self, log_dir: Path, name: str, tz: ZoneInfo) -> None:
        """``name`` is the per-kind prefix (e.g. "dreams" produces
        files like "dreams-2026-05-18.ndjson")."""
        self._log_dir = Path(log_dir)
        self._name = name
        self._tz = tz

    @property
    def name(self) -> str:
        return self._name

    def path_for_today(self) -> Path:
        today = datetime.now(self._tz).strftime("%Y-%m-%d")
        return self._log_dir / f"{self._name}-{today}.ndjson"

    def now_isoformat(self) -> str:
        return datetime.now(self._tz).isoformat()

    def append(self, record: dict[str, Any]) -> bool:
        """Append one NDJSON record. Returns True on success, False on
        failure (logged + swallowed). Sets 0600 on the file after each
        write (best-effort)."""
        path = self.path_for_today()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(record, ensure_ascii=False) + "\n"
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(line)
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            return True
        except Exception:
            log.warning("ndjson write failed: %s", path, exc_info=True)
            return False
