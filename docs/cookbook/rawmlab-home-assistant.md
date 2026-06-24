---
title: Rawmlab Home Assistant MVP
description: Minimal allowlisted Home Assistant bridge for the Rawmlab fork.
---

# Rawmlab Home Assistant MVP

The Rawmlab fork now ships a minimal Home Assistant bridge inside `dotty-pi-ext`.

It is intentionally narrow:

- one read-only tool: `home_assistant_read`
- one action tool: `home_assistant_action`
- external allowlist in JSON
- REST API only
- no MCP, no free-form entity IDs, no secret values in Git

## Environment

Set these on the `dotty-pi` container:

```env
HOME_ASSISTANT_ENABLED=true
HOME_ASSISTANT_BASE_URL=http://homeassistant.home.arpa:8123
HOME_ASSISTANT_TOKEN=change-me
HOME_ASSISTANT_TIMEOUT_SECONDS=10
HOME_ASSISTANT_CONFIG_PATH=/root/.pi/home_assistant.json
```

## Allowlist config

Start from:

[`dotty-pi-ext/home_assistant.example.json`](../../dotty-pi-ext/home_assistant.example.json)

Example:

```json
{
  "reads": {
    "office_temperature": {
      "type": "state",
      "entity_id": "sensor.office_temperature",
      "label": "Office temperature"
    }
  },
  "actions": {
    "night_mode": {
      "type": "service",
      "domain": "script",
      "service": "turn_on",
      "service_data": {
        "entity_id": "script.night_mode"
      },
      "label": "Night mode"
    }
  }
}
```

## Safety posture

- `home_assistant_read` is classified as `read_only`
- `home_assistant_action` is classified as `sensitive_action`
- actions are therefore blocked by default unless `DOTTY_ALLOW_SENSITIVE_TOOLS=true`

That means the current MVP is best suited to:

- sensor reads
- backup or homelab status checks
- explicit action testing in a controlled environment

## Logging

The bridge logs to stderr in this shape:

```text
[home_assistant] kind=read name=office_temperature status=200 duration_ms=118
[home_assistant] kind=action name=night_mode status=200 duration_ms=143
```

Errors return short voice-safe replies instead of raw traces.

## Current limitations

- no conversational confirmation state yet
- no free-form service invocation
- no dashboard UI for HA allowlist management
- no webhook mode yet
- no multi-step HA workflows
