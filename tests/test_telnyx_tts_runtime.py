"""Runtime tests for _generate_telnyx_tts.

Mocks the ``websockets`` library so no network or API key is needed.
Validates the full WebSocket protocol sequence and output file contents.
"""

from __future__ import annotations

import asyncio
import base64
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_CHUNK_1 = b"FAKEMP3CHUNK1"
FAKE_CHUNK_2 = b"FAKEMP3CHUNK2"


def _make_fake_websockets(messages: list[str]):
    """Return a fake websockets module whose connect() yields *messages*."""

    class _FakeWS:
        def __init__(self):
            self._iter = iter(messages)
            self.sent: list[str] = []

        async def send(self, data: str) -> None:
            self.sent.append(data)

        def __aiter__(self):
            return self

        async def __anext__(self) -> str:
            try:
                return next(self._iter)
            except StopIteration:
                raise StopAsyncIteration

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

    _instance = _FakeWS()

    fake_ws_module = types.ModuleType("websockets")
    fake_ws_module.connect = MagicMock(return_value=_instance)
    return fake_ws_module, _instance


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_generate_telnyx_tts_writes_audio(tmp_path, monkeypatch):
    """Happy path: receives two audio chunks, isFinal on the second."""
    messages = [
        json.dumps({"audio": base64.b64encode(FAKE_CHUNK_1).decode()}),
        json.dumps({"audio": base64.b64encode(FAKE_CHUNK_2).decode(), "isFinal": True}),
    ]
    fake_ws_module, ws_instance = _make_fake_websockets(messages)

    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.setenv("TELNYX_API_KEY", "test-key-xyz")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "tts_out.mp3"
        result = mod._generate_telnyx_tts("Hello world", str(out), {})
    finally:
        sys.path.pop(0)

    assert result == str(out)
    assert out.exists()
    assert out.read_bytes() == FAKE_CHUNK_1 + FAKE_CHUNK_2


def test_generate_telnyx_tts_sends_three_frames(tmp_path, monkeypatch):
    """The function must send exactly init, text, and stop frames."""
    messages = [
        json.dumps({"audio": base64.b64encode(b"DATA").decode(), "isFinal": True}),
    ]
    fake_ws_module, ws_instance = _make_fake_websockets(messages)

    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "out.mp3"
        mod._generate_telnyx_tts("Test text", str(out), {})
    finally:
        sys.path.pop(0)

    assert len(ws_instance.sent) == 3

    init_frame = json.loads(ws_instance.sent[0])
    assert init_frame["text"] == " "
    assert "voice" in init_frame
    assert init_frame.get("output_format") == "mp3"

    text_frame = json.loads(ws_instance.sent[1])
    assert text_frame["text"] == "Test text"

    stop_frame = json.loads(ws_instance.sent[2])
    assert stop_frame["text"] == ""


def test_generate_telnyx_tts_uses_custom_voice(tmp_path, monkeypatch):
    """Voice from tts_config should be used in the init frame."""
    messages = [
        json.dumps({"audio": base64.b64encode(b"X").decode(), "isFinal": True}),
    ]
    fake_ws_module, ws_instance = _make_fake_websockets(messages)

    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "out.mp3"
        mod._generate_telnyx_tts(
            "Hello", str(out),
            {"telnyx": {"voice": "Telnyx.KokoroTTS.af_bella"}}
        )
    finally:
        sys.path.pop(0)

    init_frame = json.loads(ws_instance.sent[0])
    assert init_frame["voice"] == "Telnyx.KokoroTTS.af_bella"


def test_generate_telnyx_tts_no_api_key_raises(tmp_path, monkeypatch):
    """Missing TELNYX_API_KEY should raise ValueError."""
    fake_ws_module, _ = _make_fake_websockets([])
    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.delenv("TELNYX_API_KEY", raising=False)

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        with pytest.raises(ValueError, match="TELNYX_API_KEY"):
            mod._generate_telnyx_tts("Hello", str(tmp_path / "out.mp3"), {})
    finally:
        sys.path.pop(0)


def test_generate_telnyx_tts_no_websockets_raises(tmp_path, monkeypatch):
    """Missing websockets package should raise ImportError with install hint."""
    monkeypatch.setitem(sys.modules, "websockets", None)  # type: ignore[arg-type]
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        with pytest.raises(ImportError, match="websockets"):
            mod._generate_telnyx_tts("Hello", str(tmp_path / "out.mp3"), {})
    finally:
        sys.path.pop(0)


def test_generate_telnyx_tts_empty_stream_raises(tmp_path, monkeypatch):
    """A stream that returns no audio chunks should raise RuntimeError."""
    messages = [json.dumps({"isFinal": True})]  # no audio field
    fake_ws_module, _ = _make_fake_websockets(messages)

    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        with pytest.raises(RuntimeError, match="no audio chunks"):
            mod._generate_telnyx_tts("Hello", str(tmp_path / "out.mp3"), {})
    finally:
        sys.path.pop(0)


def test_generate_telnyx_tts_skips_invalid_json(tmp_path, monkeypatch):
    """Non-JSON messages should be silently skipped."""
    messages = [
        "not-json",
        json.dumps({"audio": base64.b64encode(b"VALID").decode(), "isFinal": True}),
    ]
    fake_ws_module, _ = _make_fake_websockets(messages)

    monkeypatch.setitem(sys.modules, "websockets", fake_ws_module)
    monkeypatch.setenv("TELNYX_API_KEY", "test-key")

    sys.path.insert(0, str(ROOT))
    try:
        import importlib
        import telnyx_tts_provider as mod
        importlib.reload(mod)

        out = tmp_path / "out.mp3"
        mod._generate_telnyx_tts("Hello", str(out), {})
        assert out.read_bytes() == b"VALID"
    finally:
        sys.path.pop(0)
