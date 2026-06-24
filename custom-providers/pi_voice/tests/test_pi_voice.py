"""Unit tests for PiVoiceLLM — the xiaozhi LLMProvider subclass.

Focus: prompt construction (last-user extraction + sandwich injection),
first-turn / nth-turn lifecycle, error fallback path. Live pi not
required — uses a fake PiClient.
"""

from __future__ import annotations

import os
import sys
import unittest
from typing import Iterator

HERE = os.path.dirname(os.path.abspath(__file__))
PROVIDER_DIR = os.path.dirname(HERE)
CUSTOM_PROVIDERS_DIR = os.path.dirname(PROVIDER_DIR)
sys.path.insert(0, PROVIDER_DIR)
sys.path.insert(0, CUSTOM_PROVIDERS_DIR)

import textUtils  # noqa: E402
import pi_voice.pi_voice as _mod  # noqa: E402
# Import via the pi_voice package, not the top-level pi_client module —
# pi_voice catches pi_voice.pi_client.PiClientError, and `from pi_client
# import PiClientError` would give us a *different* class object even
# though the source is identical, so isinstance/except wouldn't match.
from pi_voice import LLMProvider, PiClientError, _wrap_with_sandwich  # noqa: E402
from unittest.mock import MagicMock, patch


class FakeClient:
    """Stand-in for PiClient. Captures prompts; lets tests script the
    text-delta sequence + error injection."""

    def __init__(self):
        self.prompts: list[str] = []
        self.new_session_calls = 0
        self.scripted_chunks: list[list[str]] = []
        self.scripted_errors: list[BaseException | None] = []
        self.closed = False

    def script_turn(self, chunks: list[str], error: BaseException | None = None) -> None:
        self.scripted_chunks.append(chunks)
        self.scripted_errors.append(error)

    def new_session(self) -> None:
        self.new_session_calls += 1

    def iter_turn_text(self, prompt: str) -> Iterator[str]:
        self.prompts.append(prompt)
        chunks = self.scripted_chunks.pop(0) if self.scripted_chunks else []
        err = self.scripted_errors.pop(0) if self.scripted_errors else None
        if err is not None:
            raise err
        for c in chunks:
            yield c

    def recent_stderr(self) -> list[str]:
        return []

    def close(self) -> None:
        self.closed = True


class TestSandwichInjection(unittest.TestCase):
    def test_suffix_appended_kid_mode_on(self):
        os.environ["DOTTY_KID_MODE"] = "true"
        client = FakeClient()
        client.script_turn(["😊 ", "Hi"])
        provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
        list(provider.response("sess-1", [{"role": "user", "content": "Hello"}]))
        self.assertEqual(len(client.prompts), 1)
        expected = "Hello" + textUtils.build_turn_suffix(True)
        self.assertEqual(client.prompts[0], expected)
        # Sanity: the kid-mode-specific bullets must be in the suffix.
        self.assertIn("YOUNG CHILD", client.prompts[0])
        self.assertIn("SELF-HARM EXCEPTION", client.prompts[0])

    def test_suffix_appended_kid_mode_off(self):
        os.environ["DOTTY_KID_MODE"] = "false"
        client = FakeClient()
        client.script_turn(["😐 OK"])
        provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
        list(provider.response("sess-1", [{"role": "user", "content": "Hi"}]))
        expected = "Hi" + textUtils.build_turn_suffix(False)
        self.assertEqual(client.prompts[0], expected)
        # Adult mode: still has emoji-prefix / English-only / no-Markdown
        # bullets, but NOT the kid-specific ones.
        self.assertIn("EXACTLY ONE emoji", client.prompts[0])
        self.assertNotIn("YOUNG CHILD", client.prompts[0])

    def test_wrap_helper_pure(self):
        # build_turn_suffix is the source of truth — _wrap_with_sandwich
        # is just `user + suffix`. This pins that contract so a future
        # refactor can't quietly move pre/postfix logic around.
        wrapped = _wrap_with_sandwich("hi", True)
        self.assertTrue(wrapped.startswith("hi"))
        self.assertEqual(wrapped, "hi" + textUtils.build_turn_suffix(True))


class TestEmptyTurn(unittest.TestCase):
    def test_no_user_message_short_circuits(self):
        os.environ["DOTTY_KID_MODE"] = "true"
        client = FakeClient()
        provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
        out = list(provider.response("sess-1", [{"role": "system", "content": "..."}]))
        self.assertEqual(out, ["(empty turn)"])
        self.assertEqual(client.prompts, [], "PiClient must not be called for empty dialogue")


class TestNewSessionLifecycle(unittest.TestCase):
    def test_first_turn_skips_new_session(self):
        os.environ["DOTTY_KID_MODE"] = "true"
        client = FakeClient()
        client.script_turn(["ok"])
        client.script_turn(["ok"])
        provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
        list(provider.response("s", [{"role": "user", "content": "a"}]))
        self.assertEqual(client.new_session_calls, 0, "no new_session on first turn")
        list(provider.response("s", [{"role": "user", "content": "b"}]))
        self.assertEqual(client.new_session_calls, 1, "new_session on second turn")


class TestErrorFallback(unittest.TestCase):
    def test_client_error_yields_fallback(self):
        os.environ["DOTTY_KID_MODE"] = "true"
        client = FakeClient()
        client.script_turn([], error=PiClientError("pi crashed"))
        provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
        out = list(provider.response("s", [{"role": "user", "content": "anything"}]))
        self.assertEqual(out, ["(brain offline — try again in a moment)"])


class TestObservabilityLogging(unittest.TestCase):
    def test_structured_turn_logs_include_turn_id_and_total(self):
        os.environ["DOTTY_KID_MODE"] = "true"
        os.environ.pop("DOTTY_VOICE_DEBUG", None)
        client = FakeClient()
        client.script_turn(["Hello", " world"])
        fake_logger = MagicMock()
        fake_logger.bind.return_value = fake_logger
        fake_clock = iter([10.0, 10.12, 10.4])

        with patch.object(_mod, "logger", fake_logger), \
             patch.object(_mod.time, "perf_counter", side_effect=lambda: next(fake_clock)):
            provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
            out = list(provider.response("sess-42", [{"role": "user", "content": "bonjour"}]))

        self.assertEqual("".join(out), "Hello world")
        messages = [call.args[0] for call in fake_logger.info.call_args_list]
        self.assertTrue(any("stage=turn_start" in msg for msg in messages))
        self.assertTrue(any("turn_id=sess-42-1 stage=llm_first_chunk duration_ms=120" in msg for msg in messages))
        self.assertTrue(any("turn_id=sess-42-1 stage=llm_complete" in msg and "chunks=1" in msg and "chars=11" in msg for msg in messages))
        self.assertTrue(any("turn_id=sess-42-1 stage=total duration_ms=400 outcome=ok" in msg for msg in messages))

    def test_debug_mode_logs_prompt_metadata_without_prompt_text(self):
        os.environ["DOTTY_KID_MODE"] = "false"
        os.environ["DOTTY_VOICE_DEBUG"] = "true"
        client = FakeClient()
        client.script_turn(["🙂 ok"])
        fake_logger = MagicMock()
        fake_logger.bind.return_value = fake_logger
        fake_clock = iter([20.0, 20.05, 20.1])

        with patch.object(_mod, "logger", fake_logger), \
             patch.object(_mod.time, "perf_counter", side_effect=lambda: next(fake_clock)):
            provider = LLMProvider({}, client=client)  # type: ignore[arg-type]
            list(provider.response("sess-debug", [{"role": "user", "content": "secret prompt"}]))

        messages = [call.args[0] for call in fake_logger.info.call_args_list]
        debug_msgs = [msg for msg in messages if "stage=turn_start" in msg]
        self.assertEqual(len(debug_msgs), 1)
        self.assertIn("debug=true", debug_msgs[0])
        self.assertIn("user_chars=13", debug_msgs[0])
        self.assertIn("prompt_chars=", debug_msgs[0])
        self.assertNotIn("secret prompt", debug_msgs[0])


if __name__ == "__main__":
    unittest.main()
