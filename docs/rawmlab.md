# Rawmlab Fork Notes

This fork adapts Dotty StackChan for a French-speaking HomeLab deployment while staying close to upstream.

## Remotes

- `origin` -> `https://github.com/rawmnr/dotty-stackchan`
- `upstream` -> `https://github.com/BrettKinny/dotty-stackchan`

Add the upstream remote locally if it is missing:

```bash
git remote add upstream https://github.com/BrettKinny/dotty-stackchan.git
git fetch upstream
```

## Branch posture

- `main` stays as merge-friendly as possible with upstream.
- Rawmlab-specific work should happen on short-lived feature branches.
- Keep deploy secrets and rendered runtime files out of Git.

Suggested branch names:

```text
rawmlab/mvp-persona
rawmlab/mvp-openai-compat
rawmlab/mvp-piper-fr
rawmlab/mvp-home-assistant-bridge
```

## Files to customize first

- `personas/rawmlab_homelab.md` for the adult French HomeLab persona.
- `.env` for secrets and runtime environment values.
- `data/.config.yaml` for provider selection, ASR language, TTS voice, and API endpoints.

Prefer adding Rawmlab-specific files over rewriting upstream defaults when possible.

## Safe upstream workflow

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

Before merging upstream, review changes touching:

- `custom-providers/`
- `personas/`
- `docs/`
- `docker-compose.yml.template`
- `Makefile`

These areas are the most likely to overlap with local HomeLab customization.

## Current Rawmlab path

The fork already contains the main building blocks for the MVP roadmap:

- `OpenAICompat` provider is present for OpenRouter or any OpenAI-compatible endpoint.
- `LocalPiper` provider is present for local TTS.
- `FunASR` and `WhisperLocal` are both wired for local ASR.

The first recommended fork-specific activation path is:

1. Copy `.env.example` to `.env`.
2. Copy `.config.yaml.template` to `data/.config.yaml`.
3. Set `selected_module.LLM` to `OpenAICompat` if you want a simple OpenRouter-backed MVP.
4. Set `LLM.OpenAICompat.persona_file` to `personas/rawmlab_homelab.md`.
5. Keep `selected_module.TTS: LocalPiper`; this fork now defaults to `fr_FR-upmc-medium` for local French TTS.

See also: [cookbook/rawmlab-openrouter.md](./cookbook/rawmlab-openrouter.md) for the shortest OpenRouter-backed MVP path.
See also: [cookbook/rawmlab-home-assistant.md](./cookbook/rawmlab-home-assistant.md) for the Home Assistant bridge MVP.
See also: [cookbook/rawmlab-proxmox-compose.md](./cookbook/rawmlab-proxmox-compose.md) for the Proxmox/Docker Compose deployment path.
See also: [cookbook/rawmlab-stt-fr.md](./cookbook/rawmlab-stt-fr.md) for the French STT baseline.
See also: [cookbook/rawmlab-tool-guardrails.md](./cookbook/rawmlab-tool-guardrails.md) for the current voice-tool security policy.
See also: [cookbook/rawmlab-observability.md](./cookbook/rawmlab-observability.md) for the current voice-turn diagnostics.

## Scope boundary

Keep these as fork-local concerns:

- HomeLab persona
- Home Assistant integration
- French-first defaults
- sensitive-action guardrails
- deployment notes for Proxmox or local infra

Keep these aligned with upstream whenever possible:

- core voice pipeline
- dashboard internals
- perception/event wiring
- firmware integration contracts
