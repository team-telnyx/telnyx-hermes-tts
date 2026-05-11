# Telnyx Hermes TTS Provider

Hermes speech-provider plugin for Telnyx TTS.

## Prerequisites

- Hermes Agent installed and available as `hermes`. See [Hermes Agent on GitHub](https://github.com/team-telnyx/telapps-hermes) for installation.
- `TELNYX_API_KEY` for live Telnyx TTS requests.
- Python 3.9+ only for local development/tests.

## Install

This is a copy-only Hermes plugin; `pip install .` is not required for normal use.

```bash
mkdir -p ~/.hermes/plugins/speech-providers
rm -rf ~/.hermes/plugins/speech-providers/telnyx
cp -R plugins/speech-providers/telnyx ~/.hermes/plugins/speech-providers/telnyx
```

## Configure

```bash
export TELNYX_API_KEY="KEY..."
```

Optional WebSocket URL override (e.g., for a proxy):

```bash
export TELNYX_TTS_BASE_URL="wss://your-proxy.example.com/v2/text-to-speech/speech"
```

## Verify

```bash
hermes --help
test -f ~/.hermes/plugins/speech-providers/telnyx/plugin.yaml
test -f ~/.hermes/plugins/speech-providers/telnyx/__init__.py
```

If supported by your Hermes version:

```bash
hermes providers list
```

Look for `telnyx-tts`, `telnyx-speech`, or `telnyx-voice`.

## Use

```bash
hermes tts --provider telnyx-tts --voice Telnyx.NaturalHD.astra "Hello from Telnyx!"
```

Aliases also work:

```bash
hermes tts --provider telnyx-speech --voice Telnyx.NaturalHD.luna "Soft and calm."
hermes tts --provider telnyx-voice --voice Telnyx.KokoroTTS.af_alloy "Budget voice."
```

## Troubleshooting

- `hermes: command not found` → install [Hermes Agent](https://github.com/team-telnyx/telapps-hermes) first.
- Provider not found → confirm files exist under `~/.hermes/plugins/speech-providers/telnyx/`.
- Auth failures → export a valid `TELNYX_API_KEY`.
- WebSocket errors → check network access to `wss://api.telnyx.com`.
- Python/package errors during development → use Python 3.9+ and run `python -m pytest -q`.
