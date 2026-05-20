"""Live Telnyx TTS validation (env-gated, skipped without TELNYX_API_KEY).

Validates that the real Telnyx WebSocket TTS endpoint:
1. Accepts a connection and synthesizes a short phrase.
2. Returns at least one audio chunk before isFinal.
3. The resulting file is a non-empty MP3.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY", "")
SKIP_REASON = "TELNYX_API_KEY not set — skipping live TTS tests"


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_live_synthesis_produces_audio(tmp_path):
    """A short synthesis request should produce a non-empty MP3 file."""
    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "live_tts.mp3"
        result = mod._generate_telnyx_tts(
            "Hello from Telnyx.",
            str(out),
            {},
        )
    finally:
        sys.path.pop(0)

    assert result == str(out)
    assert out.exists()
    assert out.stat().st_size > 0, "Output MP3 is empty"


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_live_synthesis_custom_voice(tmp_path):
    """Synthesis with a non-default voice should succeed."""
    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "live_voice.mp3"
        mod._generate_telnyx_tts(
            "Testing a custom voice.",
            str(out),
            {"telnyx": {"voice": "Telnyx.KokoroTTS.af_alloy"}},
        )
    finally:
        sys.path.pop(0)

    assert out.exists()
    assert out.stat().st_size > 0
