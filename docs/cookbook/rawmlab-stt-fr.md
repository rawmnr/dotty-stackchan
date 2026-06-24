---
title: Rawmlab French STT
description: Configure and validate local French speech recognition on the Rawmlab fork.
---

# Rawmlab French STT

For the Rawmlab fork, the practical default is:

- `FunASR` on CPU hosts
- `WhisperLocal` on GPU hosts
- both pinned to `language: fr`

## Why this split

- `FunASR` is lighter and simpler for a CPU-only MVP.
- `WhisperLocal` is the better fallback when French recognition quality matters more than raw setup simplicity.
- The stock upstream `small.en` Whisper model is English-only, so this fork switches to the multilingual `small` model.

## Config

The rendered `data/.config.yaml` should look like this:

```yaml
selected_module:
  ASR: FunASR

ASR:
  FunASR:
    type: fun_local
    model_dir: models/SenseVoiceSmall
    output_dir: tmp/
    language: fr

  WhisperLocal:
    type: whisper_local
    model_dir: models/whisper-small-ct2
    output_dir: tmp/
    language: fr
    model_size: small
    device: cpu
    compute_type: int8
```

On a CUDA host, `make setup` still flips the selected provider to `WhisperLocal`.

## Test phrases

Short:

- `Allume le bureau.`
- `Quelle est la température du salon ?`
- `Donne-moi le statut du HomeLab.`
- `Est-ce que les backups sont OK ?`

Longer:

- `Résume-moi les alertes importantes de Home Assistant.`
- `Demande à l'assistant local si le serveur Proxmox est stable.`

## What to look for in logs

- transcription result
- elapsed transcription time
- raw ASR metrics from `WhisperLocal` when that backend is active
- obvious language drift, especially English or East-Asian mis-detection

## MVP recommendation

- Start with `FunASR` if the host is CPU-only.
- If French commands are unreliable, switch to `WhisperLocal` first before changing the rest of the stack.
