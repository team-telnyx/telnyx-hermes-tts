---
name: telnyx-hermes-tts
description: Telnyx TTS provider contribution for Hermes Agent — integrates into tools/tts_tool.py.
metadata: {"clawdbot":{"emoji":"🔊","requires":{"env":["TELNYX_API_KEY"]},"primaryEnv":"TELNYX_API_KEY"}}
---

# Telnyx Hermes TTS Provider

Use this skill when integrating or validating the Telnyx Text-to-Speech provider for Hermes.

## Architecture

This is **not** a standalone plugin. Hermes handles TTS through built-in
providers dispatched in `tools/tts_tool.py`. This repo contains the Telnyx
provider function and tests, ready to be contributed upstream.

## Provider details

| Field | Value |
|-------|-------|
| Provider ID | `telnyx` |
| WebSocket endpoint | `wss://api.telnyx.com/v2/text-to-speech/speech` |
| Default voice | `Telnyx.NaturalHD.astra` |
| Output format | MP3 |
| Auth | `TELNYX_API_KEY` (Bearer) |
| Endpoint override | `TELNYX_TTS_BASE_URL` env var |

## Integration

See `README.md` for step-by-step instructions on adding the Telnyx TTS provider
to `tools/tts_tool.py` in hermes-agent. Requires adding `websockets` as a
dependency.

## Configure

```bash
export TELNYX_API_KEY="***"
```

Optional WebSocket URL override:

```bash
export TELNYX_TTS_BASE_URL="wss://your-proxy.example.com/v2/text-to-speech/speech"
```

## Available voices

| Family | Example voices |
|--------|---------------|
| `Telnyx.NaturalHD` | `astra`, `luna`, `orion`, `celeste`, `bond`, `andromeda` |
| `Telnyx.KokoroTTS` | `af_alloy`, `af_bella`, `am_adam`, `am_michael` |
| `Telnyx.Natural` | (see live catalog) |
| `Telnyx.Ultra` | (see live catalog) |

Full catalog: `GET /v2/text-to-speech/voices` with a valid `TELNYX_API_KEY`.

## Running tests

```bash
# No credentials needed
python -m pytest tests/test_telnyx_tts_static.py tests/test_telnyx_tts_runtime.py -q

# Live test (requires TELNYX_API_KEY)
export TELNYX_API_KEY=***
python -m pytest tests/test_telnyx_tts_live.py -q
```

## Notes

- No `pip install` needed — the provider function is copy-pasted into hermes-agent.
- Local tests use a mock WebSocket; live tests hit the real Telnyx API.
- The endpoint override (`TELNYX_TTS_BASE_URL`) is covered by tests.
