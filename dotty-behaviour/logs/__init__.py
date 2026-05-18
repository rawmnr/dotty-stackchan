"""NDJSON writers — daily-rotated append-only JSONL files for the
consumers that produce a durable trail (dreams, dances, scene-synth,
idle perception, security cycles, conversation log).

Each consumer that needs persistence owns one NdjsonWriter instance.
The writer handles rotation (one file per day under LOG_DIR/<name>-
YYYY-MM-DD.ndjson) and best-effort error swallowing (a disk-full
condition must not crash a consumer loop).
"""

from .ndjson import NdjsonWriter

__all__ = ["NdjsonWriter"]
