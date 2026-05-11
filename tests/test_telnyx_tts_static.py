"""Static validation for the standalone Telnyx TTS Hermes speech-provider plugin."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "speech-providers" / "telnyx" / "__init__.py"
MANIFEST = ROOT / "plugins" / "speech-providers" / "telnyx" / "plugin.yaml"


def _module_ast() -> ast.Module:
    return ast.parse(PLUGIN.read_text(encoding="utf-8"))


def _assigned_constant(name: str):
    for node in _module_ast().body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"missing assignment for {name}")


def test_manifest_declares_speech_provider():
    text = MANIFEST.read_text(encoding="utf-8")
    assert "kind: speech-provider" in text
    assert "name: telnyx-tts" in text


def test_provider_constants():
    assert _assigned_constant("TELNYX_TTS_DEFAULT_BASE_URL") == "wss://api.telnyx.com/v2/text-to-speech/speech"
    assert _assigned_constant("TELNYX_DEFAULT_VOICE") == "Telnyx.NaturalHD.astra"


def test_fallback_voices_contain_expected_entries():
    voices = _assigned_constant("TELNYX_FALLBACK_VOICES")
    assert voices[0] == "Telnyx.NaturalHD.astra"
    assert "Telnyx.NaturalHD.luna" in voices
    assert "Telnyx.NaturalHD.orion" in voices
    assert "Telnyx.KokoroTTS.af_alloy" in voices
    assert "Telnyx.KokoroTTS.am_adam" in voices


def test_voice_families_declared():
    families = _assigned_constant("TELNYX_TTS_VOICE_FAMILIES")
    assert "Telnyx.NaturalHD" in families
    assert "Telnyx.KokoroTTS" in families
    assert "Telnyx.Natural" in families


def test_provider_profile_shape_is_declared():
    source = PLUGIN.read_text(encoding="utf-8")
    assert 'name="telnyx-tts"' in source
    assert 'aliases=("telnyx-speech", "telnyx-voice")' in source
    assert 'env_vars=("TELNYX_API_KEY", "TELNYX_TTS_BASE_URL")' in source
    assert 'auth_type="api_key"' in source
    assert 'default_headers={"User-Agent": f"HermesAgent/{_HERMES_VERSION}"}' in source
    assert 'output_format="mp3"' in source
    assert "supports_streaming=True" in source


def test_base_url_override_from_env(monkeypatch):
    """TELNYX_TTS_BASE_URL env var should override the default."""
    import importlib.util
    import sys
    import types

    custom_url = "wss://custom.example.com/tts"
    monkeypatch.setenv("TELNYX_TTS_BASE_URL", custom_url)

    # Stub hermes_cli and providers
    hermes_cli = types.ModuleType("hermes_cli")
    hermes_cli.__version__ = "0.0-test"
    providers = types.ModuleType("providers")
    providers.register_speech_provider = lambda p: None
    providers_base = types.ModuleType("providers.base")

    class FakeSPP:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    providers_base.SpeechProviderProfile = FakeSPP
    monkeypatch.setitem(sys.modules, "hermes_cli", hermes_cli)
    monkeypatch.setitem(sys.modules, "providers", providers)
    monkeypatch.setitem(sys.modules, "providers.base", providers_base)

    spec = importlib.util.spec_from_file_location("telnyx_env_test", PLUGIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.TELNYX_TTS_BASE_URL == custom_url
    assert mod.telnyx_tts.base_url == custom_url
