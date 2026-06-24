---
title: Rawmlab Proxmox Compose
description: Minimal Docker Compose deployment for the Rawmlab fork on a Proxmox VM or Docker-ready LXC.
---

# Rawmlab Proxmox Compose

This fork now ships a Proxmox-oriented compose bundle:

- [compose.proxmox.yml](../../compose.proxmox.yml)
- [.env.proxmox.example](../../.env.proxmox.example)

Target shape:

```text
Proxmox
└── VM or Docker-ready LXC
    └── dotty-stackchan
        ├── xiaozhi-esp32-server
        ├── dotty-pi
        ├── dotty-behaviour
        └── dotty-bridge
```

## What this bundle does

It gives you one compose entrypoint for the four Dotty runtime containers:

- `xiaozhi-esp32-server`
- `dotty-pi`
- `dotty-behaviour`
- `dotty-bridge`

It also externalises:

- admin token
- Home Assistant token
- OpenRouter or VLM keys
- runtime state and logs

## What it does not hide

This bundle does **not** magically solve model serving.

You still need to choose one LLM posture:

1. `OpenAICompat` in `data/.config.yaml` for the fastest bootstrap.
2. `PiVoiceLLM` plus a prepared `dotty-pi` runtime config if you want memory, tools, and the Home Assistant bridge from voice turns.
3. Optional local backend such as llama-swap or Ollama if you want local inference.

For `dotty-pi`, the compose file starts the container, but your `/root/.pi` state still needs a valid `agent/models.json` for the backend you actually want to use.

## Ports

The bundle exposes these ports on the VM or LXC host:

| Port | Service | Purpose |
|---|---|---|
| `8000` | `xiaozhi-esp32-server` | StackChan WebSocket |
| `8003` | `xiaozhi-esp32-server` | OTA + admin HTTP |
| `8081` | `dotty-bridge` | Admin dashboard |
| `8090` | `dotty-behaviour` | Perception + voice helper API |

## Persistent paths

Default persistent paths are local bind mounts under `./runtime/`:

| Path | Purpose |
|---|---|
| `runtime/shared-state/` | shared kid/smart toggle files |
| `runtime/xiaozhi/` | OTA bins + tmp |
| `runtime/dotty-pi/` | full `PI_HOME` state, including extensions and Home Assistant allowlist |
| `runtime/dotty-behaviour/state/` | household roster, greeter state |
| `runtime/dotty-behaviour/logs/` | NDJSON logs |
| `runtime/dotty-bridge/state/` | dashboard state |
| `runtime/dotty-bridge/logs/` | dashboard logs |

Model directories remain explicit:

- `models/SenseVoiceSmall`
- `models/piper`
- `models/whisper-small.en-ct2`

## Recommended resources

For a Proxmox VM or Docker-capable LXC:

| Profile | vCPU | RAM | Disk | Notes |
|---|---|---|---|---|
| Cloud-backed MVP | 4 | 8 GB | 30 GB | `OpenAICompat`, local STT/TTS, enough for HA bridge and dashboard |
| PiVoiceLLM + external model host | 4-6 | 8-12 GB | 40 GB | keeps `dotty-pi` and its tool state local |
| Fully local with separate GPU host | 6+ | 12 GB+ | 50 GB+ | still assumes the heavy LLM backend lives elsewhere or on attached GPU infra |

For Proxmox specifically:

- prefer a VM if you want the least surprise around Docker networking and host mounts
- use an LXC only if it is already prepared for nested Docker and you accept the extra storage/networking friction

## Commands

Initial bootstrap:

```bash
cp .env.proxmox.example .env.proxmox
mkdir -p data
cp .config.yaml.template data/.config.yaml
mkdir -p runtime/xiaozhi/tmp runtime/xiaozhi/bin
mkdir -p runtime/shared-state
mkdir -p runtime/dotty-pi
mkdir -p runtime/dotty-behaviour/state runtime/dotty-behaviour/logs runtime/dotty-behaviour/secrets
mkdir -p runtime/dotty-bridge/state runtime/dotty-bridge/logs runtime/dotty-bridge/secrets
docker compose --env-file .env.proxmox -f compose.proxmox.yml up -d --build
```

Then edit `data/.config.yaml` for your chosen LLM path and LAN IP.

Operations:

```bash
docker compose --env-file .env.proxmox -f compose.proxmox.yml ps
docker compose --env-file .env.proxmox -f compose.proxmox.yml logs -f xiaozhi-server
docker compose --env-file .env.proxmox -f compose.proxmox.yml restart xiaozhi-server
docker compose --env-file .env.proxmox -f compose.proxmox.yml pull
docker compose --env-file .env.proxmox -f compose.proxmox.yml up -d --build
docker compose --env-file .env.proxmox -f compose.proxmox.yml down
```

## Home Assistant

The bundle passes `HOME_ASSISTANT_*` variables into `dotty-pi`.

To enable the Rawmlab Home Assistant bridge:

1. set `HOME_ASSISTANT_ENABLED=true` in `.env.proxmox`
2. put the allowlist JSON in `runtime/dotty-pi/home_assistant.json`
3. keep `home_assistant_action` blocked unless you intentionally enable sensitive tools

See [rawmlab-home-assistant.md](./rawmlab-home-assistant.md).

## Future homelab-infra integration

Suggested future service shape for `rawmnr/homelab-infra`:

- service name: `stackchan-assistant`
- source of truth: this repo's `compose.proxmox.yml`
- external values: `.env.proxmox`
- persistent host paths: `runtime/` subtree or infra-managed equivalents

The intended next step is to vendor or template this compose file in `homelab-infra/services/stackchan-assistant`, not to invent a second deployment topology.
