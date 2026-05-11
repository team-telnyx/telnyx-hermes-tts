"""Telnyx TTS speech provider for Hermes Agent.

Registers ``telnyx-tts`` as a first-class speech provider using the
Telnyx WebSocket-based Text-to-Speech API.  Carrier-grade latency,
NaturalHD + KokoroTTS voice families, ~10x cheaper than ElevenLabs.

Protocol (wss://api.telnyx.com/v2/text-to-speech/speech):
  1. Connect with ``Authorization: Bearer <TELNYX_API_KEY>``
  2. Send init frame:  ``{"text": " "}``
  3. Send text frame:  ``{"text": "<content>"}``
  4. Send stop frame:  ``{"text": ""}``
  5. Receive base64 mp3 chunks until ``isFinal=true``
"""

try:
    from hermes_cli import __version__ as _HERMES_VERSION
except ModuleNotFoundError as _err:
    raise ModuleNotFoundError(
        "Hermes Agent is not installed.  Install Hermes first, then copy "
        "this plugin into ~/.hermes/plugins/speech-providers/telnyx/."
    ) from _err

from providers import register_speech_provider
from providers.base import SpeechProviderProfile

# ── Constants ─────────────────────────────────────────────────────────

TELNYX_TTS_BASE_URL = "wss://api.telnyx.com/v2/text-to-speech"
TELNYX_TTS_REST_BASE_URL = "https://api.telnyx.com"
TELNYX_DEFAULT_VOICE = "Telnyx.NaturalHD.astra"

# Voice families available on Telnyx TTS.  The full catalog (950+ voices)
# is fetched live from ``GET /v2/text-to-speech/voices`` when credentials
# are present.
TELNYX_TTS_VOICE_FAMILIES = (
    "Telnyx.NaturalHD",
    "Telnyx.Natural",
    "Telnyx.KokoroTTS",
    "Telnyx.Ultra",
    "Telnyx.Qwen3TTS",
    "Telnyx.LibriTTS",
)

# Curated default/popular voices.  Used as a fallback when the live
# ``/v2/text-to-speech/voices`` endpoint is unreachable.
TELNYX_FALLBACK_VOICES = (
    # NaturalHD — premium, refined prosody
    "Telnyx.NaturalHD.astra",
    "Telnyx.NaturalHD.luna",
    "Telnyx.NaturalHD.andersen_johan",
    "Telnyx.NaturalHD.orion",
    "Telnyx.NaturalHD.celeste",
    "Telnyx.NaturalHD.bond",
    "Telnyx.NaturalHD.constance",
    "Telnyx.NaturalHD.iris",
    # KokoroTTS — budget-friendly, high-volume
    "Telnyx.KokoroTTS.af_alloy",
    "Telnyx.KokoroTTS.af_bella",
    "Telnyx.KokoroTTS.am_adam",
    "Telnyx.KokoroTTS.am_michael",
)

# ── Provider profile ──────────────────────────────────────────────────

telnyx_tts = SpeechProviderProfile(
    name="telnyx-tts",
    aliases=("telnyx-speech", "telnyx-voice"),
    display_name="Telnyx TTS",
    description=(
        "Telnyx Text-to-Speech — WebSocket streaming, NaturalHD + KokoroTTS "
        "voices, carrier-grade latency"
    ),
    signup_url="https://portal.telnyx.com/#/app/api-keys",
    env_vars=("TELNYX_API_KEY", "TELNYX_TTS_BASE_URL"),
    base_url=TELNYX_TTS_BASE_URL,
    auth_type="api_key",
    default_headers={"User-Agent": f"HermesAgent/{_HERMES_VERSION}"},
    default_voice=TELNYX_DEFAULT_VOICE,
    fallback_voices=TELNYX_FALLBACK_VOICES,
    voice_families=TELNYX_TTS_VOICE_FAMILIES,
    output_format="mp3",
    supports_streaming=True,
)

register_speech_provider(telnyx_tts)
