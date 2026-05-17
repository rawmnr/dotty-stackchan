#!/usr/bin/env python3
"""play_song matcher oracle. Outputs the matcher's decision for a query
against a candidate file list, as JSON.

Usage:
    python3 play_song_oracle.py "<query>" <file1> <file2> ...

Output:
    {"query": "...", "files": [...], "match": "<file>"|null}
"""

from __future__ import annotations

import json
import os
import sys


# Copied verbatim from bridge.py:_voice_tool_play_song_match
# (lines ~4093-4110). DO NOT refactor — this is the spec.
def _voice_tool_play_song_match(query: str, files: list[str]) -> str | None:
    if not query or not files:
        return None
    q = query.strip().lower()
    q_stem = os.path.splitext(q)[0].strip()
    best: tuple[int, str] | None = None
    for f in files:
        stem = os.path.splitext(f)[0].lower()
        if stem == q_stem:
            return f
        if q_stem and (q_stem in stem or stem in q_stem):
            score = abs(len(stem) - len(q_stem))
            if best is None or score < best[0]:
                best = (score, f)
    return best[1] if best else None


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: play_song_oracle.py <query> <file1> [file2 ...]", file=sys.stderr)
        return 2
    query = sys.argv[1]
    files = sys.argv[2:]
    match = _voice_tool_play_song_match(query, files)
    print(json.dumps({"query": query, "files": files, "match": match}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
