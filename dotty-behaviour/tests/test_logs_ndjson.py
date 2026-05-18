"""NdjsonWriter — daily rotation, atomic append, error swallowing."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from logs import NdjsonWriter


def test_append_round_trips_unicode() -> None:
    with tempfile.TemporaryDirectory() as td:
        w = NdjsonWriter(Path(td), "test", ZoneInfo("UTC"))
        assert w.append({"msg": "héllo — wörld"}) is True
        body = w.path_for_today().read_text(encoding="utf-8")
        record = json.loads(body)
        assert record["msg"] == "héllo — wörld"


def test_append_creates_log_dir() -> None:
    with tempfile.TemporaryDirectory() as td:
        nested = Path(td) / "subdir" / "logs"
        w = NdjsonWriter(nested, "test", ZoneInfo("UTC"))
        assert w.append({"k": "v"}) is True
        assert w.path_for_today().exists()


def test_path_includes_date_and_name() -> None:
    with tempfile.TemporaryDirectory() as td:
        w = NdjsonWriter(Path(td), "dreams", ZoneInfo("UTC"))
        path = w.path_for_today()
        assert path.name.startswith("dreams-")
        assert path.name.endswith(".ndjson")
        today = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%d")
        assert today in path.name


def test_multiple_appends_produce_jsonl() -> None:
    with tempfile.TemporaryDirectory() as td:
        w = NdjsonWriter(Path(td), "test", ZoneInfo("UTC"))
        w.append({"i": 1})
        w.append({"i": 2})
        lines = w.path_for_today().read_text(encoding="utf-8").splitlines()
        assert [json.loads(line) for line in lines] == [{"i": 1}, {"i": 2}]


def test_append_returns_false_on_failure() -> None:
    # Point at a path that can't be created (file as parent dir)
    with tempfile.NamedTemporaryFile() as tf:
        not_a_dir = Path(tf.name)
        w = NdjsonWriter(not_a_dir / "subdir", "test", ZoneInfo("UTC"))
        assert w.append({"k": "v"}) is False


def test_now_isoformat_returns_tz_aware_string() -> None:
    w = NdjsonWriter(Path("/tmp"), "test", ZoneInfo("UTC"))
    ts = w.now_isoformat()
    # ISO 8601 with offset suffix
    assert "+" in ts or ts.endswith("UTC") or ts.endswith("00:00")
