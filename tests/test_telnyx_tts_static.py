"""Static validation for the Telnyx TTS hermes-agent contribution.

Reads ``telnyx_tts_provider.py`` via AST — no imports, no credentials,
no network.  Validates constants, function signature, and README integration
instructions.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROVIDER = ROOT / "telnyx_tts_provider.py"
README = ROOT / "README.md"


def _module_ast() -> ast.Module:
    return ast.parse(PROVIDER.read_text(encoding="utf-8"))


def _assigned_constant(name: str):
    for node in _module_ast().body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == name:
                        return ast.literal_eval(node.value)
            else:  # AnnAssign
                if isinstance(node.target, ast.Name) and node.target.id == name and node.value:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"missing assignment for {name!r} in {PROVIDER.name}")


def test_provider_module_exists():
    assert PROVIDER.exists(), "telnyx_tts_provider.py not found in repo root"


def test_default_base_url():
    assert _assigned_constant("TELNYX_TTS_DEFAULT_BASE_URL") == \
        "wss://api.telnyx.com/v2/text-to-speech/speech"


def test_default_voice():
    assert _assigned_constant("DEFAULT_TELNYX_VOICE") == "Telnyx.NaturalHD.astra"


def test_max_text_length_reasonable():
    limit = _assigned_constant("TELNYX_TTS_MAX_TEXT_LENGTH")
    assert isinstance(limit, int)
    assert 1000 <= limit <= 50000, f"MAX_TEXT_LENGTH {limit} looks wrong"


def test_voice_families_declared():
    families = _assigned_constant("TELNYX_TTS_VOICE_FAMILIES")
    assert "Telnyx.NaturalHD" in families
    assert "Telnyx.KokoroTTS" in families


def test_fallback_voices_declared():
    voices = _assigned_constant("TELNYX_FALLBACK_VOICES")
    assert "Telnyx.NaturalHD.astra" in voices
    assert "Telnyx.KokoroTTS.af_alloy" in voices
    assert len(voices) >= 4


def test_generate_function_exists():
    source = PROVIDER.read_text(encoding="utf-8")
    assert "def _generate_telnyx_tts(" in source


def test_generate_function_signature():
    """The function must accept (text, output_path, tts_config)."""
    source = PROVIDER.read_text(encoding="utf-8")
    assert "_generate_telnyx_tts(text: str, output_path: str, tts_config" in source


def test_websocket_protocol_frames_present():
    """All three required frames must be sent in the implementation."""
    source = PROVIDER.read_text(encoding="utf-8")
    # Init frame
    assert '"text": " "' in source or '"text":" "' in source
    # Text frame
    assert '"text": text' in source or '{"text": text}' in source
    # Stop frame (empty text)
    assert '"text": ""' in source or '"text":""' in source


def test_readme_integration_instructions():
    readme = README.read_text(encoding="utf-8")
    assert "BUILTIN_TTS_PROVIDERS" in readme
    assert "PROVIDER_MAX_TEXT_LENGTH" in readme
    assert "_generate_telnyx_tts" in readme
    assert "tts_tool.py" in readme
    assert "TELNYX_API_KEY" in readme
