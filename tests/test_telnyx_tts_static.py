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
    assert "name: telnyx" in text


def test_provider_constants():
    assert _assigned_constant("TELNYX_TTS_BASE_URL") == "wss://api.telnyx.com/v2/text-to-speech"
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
