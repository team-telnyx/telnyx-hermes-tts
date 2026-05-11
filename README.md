# Telnyx TTS Provider for Hermes

Native Telnyx Text-to-Speech speech-provider plugin for Hermes Agent. It registers `telnyx-tts` as a first-class speech provider using the Telnyx WebSocket-based TTS API — carrier-grade latency, NaturalHD + KokoroTTS voices, ~10x cheaper than ElevenLabs.

## Provider

- Provider ID: `telnyx-tts`
- Plugin manifest name: `telnyx-tts`
- Aliases: `telnyx-speech`, `telnyx-voice`
- WebSocket URL: `wss://api.telnyx.com/v2/text-to-speech/speech`
- Voice catalog URL: `https://api.telnyx.com/v2/text-to-speech/voices`
- Auth env var: `TELNYX_API_KEY`
- Optional WebSocket URL override: `TELNYX_TTS_BASE_URL`
- Output format: mp3 (streaming)

## Prerequisites

- **Hermes Agent** with speech-provider plugin support installed and available on your `PATH` as `hermes`. See [Hermes Agent on GitHub](https://github.com/team-telnyx/telapps-hermes) for installation instructions.
- **Python 3.9+** for local development/tests in this repository.
- A **Telnyx API key** with access to Telnyx AI TTS.

If `hermes --help` fails, install Hermes Agent first, then return to these steps. This repository only contains the Telnyx TTS provider plugin; it does not install Hermes itself.

## Install

This is a copy-only Hermes plugin. `pip install .` is **not required** for normal use — it only installs package metadata, not the plugin itself. The plugin must be copied into the Hermes plugin directory.

From the repository root, copy the bundled speech-provider plugin into Hermes' plugin directory:

```bash
mkdir -p ~/.hermes/plugins/speech-providers
rm -rf ~/.hermes/plugins/speech-providers/telnyx
cp -R plugins/speech-providers/telnyx ~/.hermes/plugins/speech-providers/telnyx
```

Then configure your Telnyx API key:

```bash
export TELNYX_API_KEY="KEY..."
```

Optional: point Hermes at a non-production Telnyx-compatible TTS endpoint:

```bash
export TELNYX_TTS_BASE_URL="wss://your-proxy.example.com/v2/text-to-speech/speech"
```

## Verify installation without credentials

First confirm Hermes is installed:

```bash
hermes --help
```

Then confirm the plugin files landed in the directory Hermes scans:

```bash
test -f ~/.hermes/plugins/speech-providers/telnyx/plugin.yaml
test -f ~/.hermes/plugins/speech-providers/telnyx/__init__.py
```

If your Hermes build has a provider-listing command:

```bash
hermes providers list
```

Look for `telnyx-tts`, `telnyx-speech`, or `telnyx-voice`.

## Use

```bash
hermes tts --provider telnyx-tts --voice Telnyx.NaturalHD.astra "Hello from Telnyx!"
```

You can also use the aliases:

```bash
hermes tts --provider telnyx-speech --voice Telnyx.NaturalHD.luna "Soft and calm."
hermes tts --provider telnyx-voice --voice Telnyx.KokoroTTS.af_alloy "Budget-friendly voice."
```

## Voice families

| Family | Description | Use case |
|--------|-------------|----------|
| **NaturalHD** | Premium, refined prosody | Production, demos, voice agents |
| **Natural** | Standard voices | General-purpose |
| **KokoroTTS** | Budget-friendly, fast synthesis | High-volume, batch processing |
| **Ultra** | Ultra-high-quality (may require specific tier) | Premium applications |
| **Qwen3TTS** | Experimental multilingual voices | Multilingual applications |
| **LibriTTS** | Small, functional audio output | Lightweight applications |

### Popular voices

| Voice ID | Family | Description |
|----------|--------|-------------|
| `Telnyx.NaturalHD.astra` | NaturalHD | Female, warm and clear (default) |
| `Telnyx.NaturalHD.luna` | NaturalHD | Female, soft and calm |
| `Telnyx.NaturalHD.orion` | NaturalHD | Male, deep and authoritative |
| `Telnyx.NaturalHD.celeste` | NaturalHD | Female, clear |
| `Telnyx.NaturalHD.bond` | NaturalHD | Male, confident |
| `Telnyx.NaturalHD.andromeda` | NaturalHD | Female, expressive |
| `Telnyx.NaturalHD.estelle` | NaturalHD | Female, warm |
| `Telnyx.NaturalHD.baldur` | NaturalHD | Male, strong |
| `Telnyx.KokoroTTS.af_alloy` | KokoroTTS | Female, budget |
| `Telnyx.KokoroTTS.af_bella` | KokoroTTS | Female alternative |
| `Telnyx.KokoroTTS.am_adam` | KokoroTTS | Male, budget |
| `Telnyx.KokoroTTS.am_michael` | KokoroTTS | Male alternative |

To browse the full voice catalog (950+ voices), query the Telnyx TTS voices endpoint:

```bash
curl -s https://api.telnyx.com/v2/text-to-speech/voices \
  -H "Authorization: Bearer $TELNYX_API_KEY" | jq '.voices[].id'
```

This plugin declares 12 curated fallback voices for offline discovery. Hermes may fetch the full catalog at runtime depending on the speech-provider contract.

## Troubleshooting

### `hermes: command not found`

Hermes Agent is not installed or is not on your `PATH`. See [Hermes Agent on GitHub](https://github.com/team-telnyx/telapps-hermes) for installation.

### Provider is not found by Hermes

Re-copy the plugin from the repository root and make sure the final path is exactly:

```text
~/.hermes/plugins/speech-providers/telnyx/plugin.yaml
~/.hermes/plugins/speech-providers/telnyx/__init__.py
```

Avoid copying the parent `plugins/` directory into `~/.hermes`; Hermes expects speech-provider plugins under `~/.hermes/plugins/speech-providers/<provider-id>`.

### `TELNYX_API_KEY` is missing or unauthorized

Set a Telnyx API key before making TTS requests:

```bash
export TELNYX_API_KEY="KEY..."
```

Create or rotate keys in the [Telnyx Mission Control Portal](https://portal.telnyx.com/#/app/api-keys).

### WebSocket connection errors

- Ensure `wss://api.telnyx.com` is reachable from your network.
- Check for firewall/proxy rules blocking WebSocket connections.
- Try the optional `TELNYX_TTS_BASE_URL` override if using a proxy.

### Python version errors during development

This repository supports Python 3.9+ for local test environments. If your system `python3` is older:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pytest
python -m pytest -q
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip pytest
python -m pytest -q
```

The tests include:

- **Static tests** — manifest shape, provider constants, voice families, and provider profile shape validation via AST parsing. No imports, no Hermes required.
- **Runtime smoke test** — stubs the Hermes provider API, imports the plugin, and verifies provider registration with correct name, aliases, base URL, auth type, voices, and streaming support.
- **Env-gated live tests** — validate the voice catalog against the real Telnyx TTS API. Requires `TELNYX_API_KEY`. Skipped by default.

> **Note:** These tests validate the plugin's shape, constants, and provider registration contract. End-to-end TTS synthesis testing requires a running Hermes Agent with the plugin installed.

## WebSocket TTS protocol

The Telnyx TTS API uses a WebSocket-based streaming protocol:

```text
Client                                 Telnyx TTS
  │                                        │
  │── wss://...speech?voice=Telnyx.NaturalHD.astra─▶│
  │   Authorization: Bearer <key>          │
  │                                        │
  │── {"text": " "}  (init frame) ────────▶│
  │── {"text": "Hello!"} (text frame) ───▶│
  │── {"text": ""}  (stop frame) ─────────▶│
  │                                        │
  │◀── {audio: "<base64 mp3>", text: null} │  streaming chunks
  │◀── {audio: "<base64 mp3>", text: null} │
  │◀── {isFinal: true} ──────────────────│  done
  │                                        │
```

## Related

- Linear: AIF-193
- OpenClaw equivalent: AIF-122 / `team-telnyx/telnyx-openclaw-tts`
