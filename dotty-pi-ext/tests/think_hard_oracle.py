#!/usr/bin/env python3
"""think_hard request-body oracle. Outputs the exact dict that bridge.py
would POST to llama-swap for a given question, as JSON.

Usage:
    python3 think_hard_oracle.py "<question>"

The TS test loads this JSON and asserts buildThinkRequest produces the
same shape (model name aside — we pin it on both sides). Body equivalence
is what the oracle covers; the LLM response itself isn't deterministic
so the TS test handles success/timeout/error paths separately via mocks.
"""

from __future__ import annotations

import json
import os
import sys


# Copied verbatim from bridge.py:_voice_tool_think_hard inner _post()
# (lines ~4008-4030). Do NOT refactor — this is the spec.
def build_think_request(question: str, model: str | None = None) -> dict:
    return {
        "model": model or os.environ.get("VOICE_THINKER_MODEL", "qwen3.6:27b-think"),
        "messages": [
            {"role": "system", "content":
                "Answer the user's question concisely in 1-2 sentences. Be precise."},
            {"role": "user", "content": question},
        ],
        "max_tokens": 200,
        "temperature": 0.3,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": False},
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: think_hard_oracle.py <question>", file=sys.stderr)
        return 2
    question = sys.argv[1]
    body = build_think_request(question)
    print(json.dumps(body, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
