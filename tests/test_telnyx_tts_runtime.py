"""Runtime smoke test for the Telnyx TTS Hermes speech-provider plugin.

Stubs the minimal Hermes modules the plugin imports, then loads the
plugin exactly as Hermes' plugin discovery would — verifying that the
provider registers correctly without requiring Hermes to be installed.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "speech-providers" / "telnyx" / "__init__.py"


def test_plugin_import_registers_telnyx_tts_provider(monkeypatch):
    registered = []

    # Stub hermes_cli
    hermes_cli = types.ModuleType("hermes_cli")
    hermes_cli.__version__ = "0.0-test"

    # Stub providers
    providers = types.ModuleType("providers")

    def register_speech_provider(profile):
        registered.append(profile)

    providers.register_speech_provider = register_speech_provider

    # Stub providers.base
    providers_base = types.ModuleType("providers.base")

    class SpeechProviderProfile:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            for key, value in kwargs.items():
                setattr(self, key, value)

    providers_base.SpeechProviderProfile = SpeechProviderProfile

    monkeypatch.setitem(sys.modules, "hermes_cli", hermes_cli)
    monkeypatch.setitem(sys.modules, "providers", providers)
    monkeypatch.setitem(sys.modules, "providers.base", providers_base)

    spec = importlib.util.spec_from_file_location("telnyx_tts_runtime_test", PLUGIN)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert len(registered) == 1
    profile = registered[0]

    # Provider identity
    assert profile.name == "telnyx-tts"
    assert profile.aliases == ("telnyx-speech", "telnyx-voice")

    # API configuration
    assert profile.base_url == "wss://api.telnyx.com/v2/text-to-speech"
    assert profile.auth_type == "api_key"
    assert profile.env_vars == ("TELNYX_API_KEY", "TELNYX_TTS_BASE_URL")
    assert profile.default_headers == {"User-Agent": "HermesAgent/0.0-test"}

    # Voice configuration
    assert profile.default_voice == "Telnyx.NaturalHD.astra"
    assert "Telnyx.NaturalHD.luna" in profile.fallback_voices
    assert "Telnyx.KokoroTTS.af_alloy" in profile.fallback_voices

    # Skills
    assert profile.output_format == "mp3"
    assert profile.supports_streaming is True
