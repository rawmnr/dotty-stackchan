---
title: Rawmlab Voice Observability
description: Minimal voice-turn observability for the Rawmlab fork.
---

# Rawmlab Voice Observability

The Rawmlab fork now emits structured voice-turn logs on these shipped providers:

- `PiVoiceLLM` for the normal `dotty-pi` path
- `OpenAICompat` for the OpenRouter or OpenAI-compatible MVP path
- `FunASRLocal` and `WhisperLocal` for local STT
- `LocalPiper` and `EdgeStream` for TTS

Current scope is still intentionally lightweight:

- one `turn_id` per voice interaction
- first-token latency
- LLM completion duration
- total turn duration as seen by the LLM provider
- STT start, retry, and completion timing
- TTS start, per-segment timing, and per-turn completion timing
- optional debug metadata without prompt text or API secrets

This is the first slice of issue `#11`, not the full audio, STT, TTS, and device-level observability story yet.

## Log shape

Normal logs now follow this pattern:

```text
turn_id=sess-42-7 stage=turn_start ...
turn_id=sess-42-7 stage=llm_first_chunk duration_ms=412
turn_id=sess-42-7 stage=llm_complete duration_ms=1834 chunks=3 chars=71 outcome=ok
turn_id=sess-42-7 stage=total duration_ms=1834 outcome=ok
```

Local STT logs now follow this pattern:

```text
turn_id=sess-42-stt-7 stage=stt_start session_id='sess-42' audio_bytes=49152 language='fr'
turn_id=sess-42-stt-7 stage=stt_retry duration_ms=801 attempt=1 error_type=OSError
turn_id=sess-42-stt-7 stage=stt_complete duration_ms=1264 retries=1 text_chars=31 outcome=ok
```

`PiVoiceLLM` also logs:

```text
turn_id=sess-42-8 stage=new_session duration_ms=37
```

That makes it easier to distinguish:

- delayed reset inside the long-lived `pi` process
- slow first token from the model
- a longer full answer after a fast first token

Local TTS logs follow this pattern:

```text
turn_id=sess-42-tts-7 stage=tts_start session_id='sess-42' voice='fr_FR-upmc-medium'
turn_id=sess-42-tts-7 stage=tts_segment duration_ms=218 text_chars=42 audio_bytes=28704 is_last=True outcome=ok
turn_id=sess-42-tts-7 stage=tts_complete duration_ms=231 segments=1 chars=42 outcome=ok
```

## Enable debug mode

Set this env var on the `xiaozhi-esp32-server` container:

```env
DOTTY_VOICE_DEBUG=true
```

Debug mode adds safe metadata such as:

- `dialogue_messages`
- `prompt_messages`
- `user_chars`
- `prompt_chars`
- sanitized `url` on `OpenAICompat`

It does **not** log:

- raw prompt text
- API keys
- URL query strings

## Reading a slow turn

Use this order:

1. Find a `stage=total` line with an unusually high `duration_ms`.
2. Match the same `turn_id`.
3. Compare `llm_first_chunk` against `llm_complete`.

Interpretation:

- high `llm_first_chunk`, high `total`: model or upstream endpoint is slow to start
- low `llm_first_chunk`, high `total`: the answer streamed promptly but took time to finish
- high `new_session`: long-lived `pi` reset is contributing before generation begins
- high `stt_complete`: local speech recognition is the bottleneck
- repeated `stt_retry`: model/runtime or audio handling is unstable
- high `tts_segment`: synthesis itself is slow
- low `tts_segment` but high `tts_complete`: queueing or segmentation overhead is contributing
- `outcome=error`: inspect nearby provider errors and `pi.stderr` lines

## Current limitations

This slice does not yet give you:

- wake-word latency
- audio capture duration
- device disconnect correlation
- dashboard summaries

Those still need separate instrumentation in xiaozhi patches, ASR/TTS providers, or the dashboard service.
