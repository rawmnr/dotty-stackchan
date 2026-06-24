import importlib.util as _ilu
import pathlib
import sys
import unittest


_PY = (
    pathlib.Path(__file__).parent.parent
    / "custom-providers"
    / "voice_observability.py"
)
_spec = _ilu.spec_from_file_location("voice_observability_under_test", _PY)
_mod = _ilu.module_from_spec(_spec)  # type: ignore[arg-type]
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]


class TestHelpers(unittest.TestCase):
    def test_make_turn_id_sanitizes_session(self):
        turn_id = _mod.make_turn_id("sess 42:/abc", "stt", 3)
        self.assertEqual(turn_id, "sess_42__abc-stt-3")

    def test_elapsed_ms_rounds(self):
        self.assertEqual(_mod.elapsed_ms(10.0, clock=lambda: 10.1244), 124)
        self.assertEqual(_mod.elapsed_ms(10.0, clock=lambda: 10.1246), 125)


class TestStreamingTurnTracker(unittest.TestCase):
    def test_tracker_counts_segments_and_chars(self):
        clock = iter([1.0, 1.35])
        tracker = _mod.StreamingTurnTracker("tts", clock=lambda: next(clock))
        turn_id = tracker.begin("sess-1")
        tracker.note_segment("hello")
        tracker.note_segment(" world")

        summary = tracker.finish()

        self.assertEqual(turn_id, "sess-1-tts-1")
        self.assertEqual(summary.turn_id, "sess-1-tts-1")
        self.assertEqual(summary.duration_ms, 350)
        self.assertEqual(summary.segments, 2)
        self.assertEqual(summary.chars, 11)
        self.assertIsNone(tracker.current_turn_id())

    def test_finish_without_begin_is_none(self):
        tracker = _mod.StreamingTurnTracker("tts")
        self.assertIsNone(tracker.finish())


if __name__ == "__main__":
    unittest.main()
