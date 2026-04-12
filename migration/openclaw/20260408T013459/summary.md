# OpenClaw -> Hermes Migration Report

- Timestamp: 20260408T013459
- Mode: execute
- Source: `/root/.openclaw`
- Target: `/root/.hermes`

## Summary

- migrated: 10
- archived: 10
- skipped: 26
- conflict: 0
- error: 0

## What Was Not Fully Brought Over

- `/root/.openclaw/workspace/AGENTS.md` -> `(n/a)`: No workspace target was provided
- `(n/a)` -> `/root/.hermes/memories/MEMORY.md`: Source file not found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/.env`: No Discord settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/.env`: No Slack settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/.env`: No WhatsApp settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/.env`: No Signal settings found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/.env`: No provider API keys found
- `/root/.openclaw/openclaw.json` -> `/root/.hermes/config.yaml`: No TTS configuration found in OpenClaw config
- `(n/a)` -> `/root/.hermes/config.yaml`: No OpenClaw exec approvals file found
- `(n/a)` -> `/root/.hermes/skills/openclaw-imports`: No shared OpenClaw skills directories found
- `(n/a)` -> `/root/.hermes/tts`: Source directory not found
- `/root/.openclaw/openclaw.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw OpenClaw config was not copied.
- `/root/.openclaw/credentials/telegram-default-allowFrom.json` -> `(n/a)`: Selected Hermes-compatible values were extracted; raw credentials file was not copied.
- `/root/.openclaw/memory/main.sqlite` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/credentials` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/devices` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `/root/.openclaw/identity` -> `(n/a)`: Contains secrets, binary state, or product-specific runtime data
- `(n/a)` -> `(n/a)`: No MCP servers found in OpenClaw config
- `(n/a)` -> `(n/a)`: No cron configuration found
- `(n/a)` -> `(n/a)`: No hooks configuration found
- `(n/a)` -> `(n/a)`: No browser configuration found
- `(n/a)` -> `(n/a)`: No approvals configuration found
- `(n/a)` -> `(n/a)`: No memory backend configuration found
- `(n/a)` -> `(n/a)`: No skills registry configuration found
- `(n/a)` -> `(n/a)`: No UI/identity configuration found
- `(n/a)` -> `(n/a)`: No logging/diagnostics configuration found
