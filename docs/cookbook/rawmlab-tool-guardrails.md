---
title: Rawmlab Tool Guardrails
description: Security policy for Dotty voice tools on the Rawmlab fork.
---

# Rawmlab Tool Guardrails

The Rawmlab fork now wraps `dotty-pi-ext` voice tools in a central guardrail policy.

## Default behaviour

- `read_only` tools are allowed
- `safe_action` tools are allowed
- `sensitive_action` tools are blocked by default
- unknown or unclassified tools are blocked by default

Current default classification:

- `home_assistant_read` -> `read_only`
- `home_assistant_action` -> `sensitive_action`
- `memory_lookup` -> `read_only`
- `recall_person` -> `read_only`
- `think_hard` -> `read_only`
- `play_song` -> `safe_action`
- `remember` -> `safe_action`
- `remember_person` -> `safe_action`
- `take_photo` -> `sensitive_action`

## Environment controls

Optional env vars for the `dotty-pi` container:

```env
DOTTY_TOOL_ALLOWLIST=memory_lookup,think_hard,play_song
DOTTY_TOOL_DENYLIST=take_photo
DOTTY_ALLOW_SENSITIVE_TOOLS=false
```

Rules:

- `DOTTY_TOOL_DENYLIST` always wins
- if `DOTTY_TOOL_ALLOWLIST` is set, any omitted tool is blocked
- `DOTTY_ALLOW_SENSITIVE_TOOLS=true` is required before a sensitive tool can execute at all

## Logging

Each tool decision is logged to stderr in this shape:

```text
[guardrails] tool=take_photo risk=sensitive_action allowed=false reason=sensitive_requires_confirmation_path
```

## Important limitation

This slice does **not** implement a full conversational `pending_confirmation` state yet.

Instead, it takes the stricter posture:

- sensitive tools are blocked until a real confirmation path exists
- this prevents accidental execution against future Home Assistant or infra actions
