# Telnyx TTS Provider for Hermes

Native Telnyx Text-to-Speech speech-provider plugin for Hermes Agent. It registers `telnyx-tts` as a first-class speech provider using the Telnyx WebSocket-based TTS API — carrier-grade latency, NaturalHD + KokoroTTS voices, ~10x cheaper than ElevenLabs.

## Provider

- Provider ID: `telnyx-tts`
- Aliases: `telnyx-speech`, `telnyx-voice`
- WebSocket URL: `wss://api.telnyx.com/v2/text-to-speech/speech`
- Voice catalog URL: `https://api.telnyx.com/v2/text-to-speech/voices`
- Auth env var: `TELNYX_API_KEY`
- Optional WebSocket URL override: `TELNYX_TTS_BASE_URL`
- Output format: mp3 (streaming)

## Prerequisites

- Hermes Agent with speech-provider plugin support installed and available on your `PATH` as `hermes`.
- Python 3.10+ for local development/tests in this repository.
- A Telnyx API key with access to Telnyx AI TTS.

If `hermes --help` fails, install Hermes Agent first, then return to these steps. This repository only contains the Telnyx TTS provider plugin; it does not install Hermes itself.

## Install

This is a copy-only Hermes plugin. `pip install .` is **not required** for normal use.

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
export TELNYX_TTS_BASE_URL="wss://api.telnyx.com/v2/text-to-speech"
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
| `Telnyx.NaturalHD.andersen_johan` | NaturalHD | Male, professional |
| `Telnyx.NaturalHD.orion` | NaturalHD | Male, deep and authoritative |
| `Telnyx.NaturalHD.celeste` | NaturalHD | Female, clear |
| `Telnyx.NaturalHD.bond` | NaturalHD | Male, confident |
| `Telnyx.NaturalHD.constance` | NaturalHD | Female, confident |
| `Telnyx.NaturalHD.iris` | NaturalHD | Female, friendly and bright |
| `Telnyx.KokoroTTS.af_alloy` | KokoroTTS | Female, budget |
| `Telnyx.KokoroTTS.af_bella` | KokoroTTS | Female alternative |
| `Telnyx.KokoroTTS.am_adam` | KokoroTTS | Male, budget |
| `Telnyx.KokoroTTS.am_michael` | KokoroTTS | Male alternative |

The full catalog (950+ voices) is fetched live from `GET /v2/text-to-speech/voices` when `TELNYX_API_KEY` is set.

## Troubleshooting

### `hermes: command not found`

Hermes Agent is not installed or is not on your `PATH`. Install Hermes first, then re-run `hermes --help`.

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

This repository requires Python 3.10+ for local test environments. If your system `python3` is older:

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

- Static manifest/provider shape checks.
- A runtime import smoke test using stubbed Hermes provider APIs, so provider registration is validated even when Hermes is not installed in the test environment.
- Env-gated live tests that validate the voice catalog against the real Telnyx TTS API (requires `TELNYX_API_KEY`).

## WebSocket TTS protocol

The Telnyx TTS API uses a WebSocket-based streaming protocol:

```text
Client                                 Telnyx TTS
  │                                        │
  │── wss://...speech?voice=NaturalHD.astra──▶│
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
- OCPlatform equivalent: AIF-122 / `team-telnyx/telnyx-openclaw-tts`
