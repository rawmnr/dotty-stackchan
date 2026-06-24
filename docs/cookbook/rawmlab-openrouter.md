---
title: Rawmlab OpenRouter MVP
description: Switch the Rawmlab fork to the OpenAI-compatible provider with OpenRouter, without changing code.
---

# Rawmlab OpenRouter MVP

For the Rawmlab fork, the fastest MVP path is:

- local ASR
- local Piper TTS
- `OpenAICompat` for the LLM
- `personas/rawmlab_homelab.md` for the voice persona

This keeps the setup simple while preserving a clean migration path later to Ollama, llama-swap, LM Studio, or vLLM.

## 1. Set the secret

In `.env`, set:

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Do not commit real keys.

## 2. Enable `OpenAICompat`

Edit `data/.config.yaml`:

```yaml
selected_module:
  LLM: OpenAICompat

LLM:
  OpenAICompat:
    type: openai_compat
    url: https://openrouter.ai/api/v1
    api_key: sk-or-v1-...
    model: openai/gpt-4o-mini
    persona_file: personas/rawmlab_homelab.md
    max_tokens: 256
    temperature: 0.4
    timeout: 60
```

The backend remains code-free to swap later. Only `url`, `api_key`, and `model` change.

## 3. For a local endpoint later

Keep the same provider and replace only the endpoint block:

```yaml
LLM:
  OpenAICompat:
    type: openai_compat
    url: http://<LOCAL_LLM_HOST>:11434/v1
    api_key: unused
    model: qwen3:8b
    persona_file: personas/rawmlab_homelab.md
```

Examples of compatible local backends:

- Ollama
- llama-swap
- LM Studio
- vLLM

## 4. Restart and verify

```bash
docker compose restart xiaozhi-server
```

Expected behaviour:

- replies stay in French
- replies stay short and voice-friendly
- sensitive actions trigger explicit confirmation
- xiaozhi-server logs show the model, elapsed time, and API failures from `OpenAICompat`

## Notes

- `PiVoiceLLM` remains the richer path if you want memory and tools.
- `OpenAICompat` is the simpler MVP path if you want to validate the voice stack first.
