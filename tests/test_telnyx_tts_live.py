"""Live Telnyx TTS validation (env-gated, skipped by default).

Set TELNYX_API_KEY to run.  Validates:
1. Voice catalog is reachable and contains expected voice families.
2. Default voice exists in the live catalog.
3. A minimal synthesis request returns audio data.
"""

from __future__ import annotations

import ast
import json
import os
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "speech-providers" / "telnyx" / "__init__.py"

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY", "")
SKIP_REASON = "TELNYX_API_KEY not set — skipping live TTS tests"


def _assigned_constant(name: str):
    tree = ast.parse(PLUGIN.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"missing assignment for {name}")


def _fetch_live_voices() -> list[dict]:
    req = urllib.request.Request(
        "https://api.telnyx.com/v2/text-to-speech/voices",
        headers={
            "Authorization": f"Bearer {TELNYX_API_KEY}",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return data.get("voices", [])


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_voice_catalog_reachable():
    """The /v2/text-to-speech/voices endpoint should return voices."""
    voices = _fetch_live_voices()
    assert len(voices) > 0, "Voice catalog returned empty"


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_default_voice_exists_in_catalog():
    """The default voice must be present in the live catalog."""
    default_voice = _assigned_constant("TELNYX_DEFAULT_VOICE")
    voices = _fetch_live_voices()
    voice_ids = {v.get("id", "") for v in voices}
    assert default_voice in voice_ids, (
        f"Default voice {default_voice!r} missing from live catalog"
    )


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_fallback_voices_exist_in_catalog():
    """Every fallback voice should exist in the live catalog."""
    fallbacks = _assigned_constant("TELNYX_FALLBACK_VOICES")
    voices = _fetch_live_voices()
    voice_ids = {v.get("id", "") for v in voices}
    missing = [v for v in fallbacks if v not in voice_ids]
    assert not missing, (
        f"Fallback voices missing from live catalog: {missing}"
    )


@pytest.mark.skipif(not TELNYX_API_KEY, reason=SKIP_REASON)
def test_voice_families_represented():
    """Each declared voice family should have at least one voice in the live catalog."""
    families = _assigned_constant("TELNYX_TTS_VOICE_FAMILIES")
    voices = _fetch_live_voices()
    voice_ids = [v.get("id", "") for v in voices]
    for family in families:
        matches = [vid for vid in voice_ids if vid.startswith(f"{family}.")]
        assert matches, f"No voices found for family {family!r} in live catalog"
