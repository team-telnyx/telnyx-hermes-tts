"""Telnyx TTS built-in provider for Hermes Agent.

This module is a **contribution to hermes-agent**, not a standalone plugin.
It contains the implementation that should be integrated into
``tools/tts_tool.py`` in the `team-telnyx/hermes-agent
<https://github.com/team-telnyx/hermes-agent>`_ repository.

Integration steps
-----------------
See README.md for the full patch instructions.  In brief:

1. Add ``"telnyx"`` to ``BUILTIN_TTS_PROVIDERS`` in ``tts_tool.py``.
2. Add ``"telnyx": 5000`` to ``PROVIDER_MAX_TEXT_LENGTH``.
3. Copy ``_generate_telnyx_tts`` into ``tts_tool.py`` (near the other
   ``_generate_*`` functions).
4. Add the dispatch branch in ``text_to_speech_tool``:

   .. code-block:: python

       elif provider == "telnyx":
           logger.info("Generating speech with Telnyx TTS...")
           _generate_telnyx_tts(text, file_str, tts_config)

5. Install the ``websockets`` dependency::

       pip install websockets

WebSocket protocol
------------------
1. Connect to ``wss://api.telnyx.com/v2/text-to-speech/speech``
   with ``Authorization: Bearer <TELNYX_API_KEY>``.
2. Send init frame:  ``{"text": " ", "voice": "<voice>", "output_format": "mp3"}``
3. Send text frame:  ``{"text": "<your text>"}``
4. Send stop frame:  ``{"text": ""}``  (empty text = end-of-input signal)
5. Receive JSON messages containing a base64-encoded ``audio`` field until
   ``isFinal`` is ``true``; decode and concatenate to produce the MP3 file.

Configuration (``~/.hermes/config.yaml`` under ``tts.telnyx``)
--------------------------------------------------------------
.. code-block:: yaml

    tts:
      provider: telnyx
      telnyx:
        voice: Telnyx.NaturalHD.astra     # optional, this is the default
        base_url: wss://...               # optional endpoint override

Environment variables
---------------------
``TELNYX_API_KEY``
    Required — Bearer token (create at https://portal.telnyx.com/#/app/api-keys).
``TELNYX_TTS_BASE_URL``
    Optional — override the WebSocket endpoint.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import ssl
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# ── Constants (add/merge these into tools/tts_tool.py) ────────────────────

TELNYX_TTS_DEFAULT_BASE_URL = "wss://api.telnyx.com/v2/text-to-speech/speech"
DEFAULT_TELNYX_VOICE = "Telnyx.NaturalHD.astra"
TELNYX_TTS_MAX_TEXT_LENGTH = 5000  # conservative; no published hard cap

# Curated voice catalog for offline discovery / documentation.
TELNYX_TTS_VOICE_FAMILIES = (
    "Telnyx.NaturalHD",
    "Telnyx.Natural",
    "Telnyx.KokoroTTS",
    "Telnyx.Ultra",
    "Telnyx.Qwen3TTS",
    "Telnyx.LibriTTS",
)

TELNYX_FALLBACK_VOICES = (
    "Telnyx.NaturalHD.astra",
    "Telnyx.NaturalHD.luna",
    "Telnyx.NaturalHD.orion",
    "Telnyx.NaturalHD.celeste",
    "Telnyx.NaturalHD.bond",
    "Telnyx.NaturalHD.andromeda",
    "Telnyx.NaturalHD.estelle",
    "Telnyx.NaturalHD.baldur",
    "Telnyx.KokoroTTS.af_alloy",
    "Telnyx.KokoroTTS.af_bella",
    "Telnyx.KokoroTTS.am_adam",
    "Telnyx.KokoroTTS.am_michael",
)


# ── Env helper ────────────────────────────────────────────────────────────
# In tts_tool.py this function already exists at module level.
# This copy is only used when running this file standalone / in tests.

def _get_env_value(name: str, default: str | None = None) -> str | None:
    """Read env values; defers to hermes_cli.config when available."""
    try:
        from hermes_cli.config import get_env_value as _gev
    except ImportError:
        return os.getenv(name, default)
    val = _gev(name)
    return default if val is None else val


# ── Provider implementation ────────────────────────────────────────────────

def _generate_telnyx_tts(text: str, output_path: str, tts_config: Dict[str, Any]) -> str:
    """Generate audio using the Telnyx WebSocket TTS API.

    Drop this function into ``tools/tts_tool.py`` alongside the other
    ``_generate_*`` helpers, then add the dispatch branch described in the
    module docstring.

    Note: when integrated into ``tts_tool.py``, replace the call to
    ``_get_env_value`` with the existing module-level ``get_env_value``.

    Args:
        text:        The text to synthesize.
        output_path: Destination path for the MP3 file.
        tts_config:  The ``tts`` section from ``~/.hermes/config.yaml``.

    Returns:
        The value of ``output_path``.

    Raises:
        ImportError:  If ``websockets`` is not installed.
        ValueError:   If ``TELNYX_API_KEY`` is not set.
        RuntimeError: If the WebSocket stream closes without yielding audio.
    """
    try:
        import websockets  # noqa: PLC0415
    except ImportError:
        raise ImportError(
            "Telnyx TTS requires the 'websockets' package. "
            "Install it with:  pip install websockets"
        )

    # In tts_tool.py use the existing get_env_value; here use _get_env_value.
    _env = _get_env_value
    api_key = (_env("TELNYX_API_KEY") or "").strip()
    if not api_key:
        raise ValueError(
            "TELNYX_API_KEY is not set. "
            "Create an API key at https://portal.telnyx.com/#/app/api-keys"
        )

    telnyx_cfg = tts_config.get("telnyx", {})
    voice = (
        str(telnyx_cfg.get("voice") or DEFAULT_TELNYX_VOICE).strip()
        or DEFAULT_TELNYX_VOICE
    )
    ws_url = str(
        telnyx_cfg.get("base_url")
        or _env("TELNYX_TTS_BASE_URL")
        or TELNYX_TTS_DEFAULT_BASE_URL
    ).strip()

    async def _stream() -> List[bytes]:
        ssl_ctx = ssl.create_default_context()
        async with websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {api_key}"},
            ssl=ssl_ctx,
            open_timeout=15,
            close_timeout=10,
        ) as ws:
            # 1. Init frame — declares voice and desired output format
            await ws.send(json.dumps({
                "text": " ",
                "voice": voice,
                "output_format": "mp3",
            }))
            # 2. Text frame
            await ws.send(json.dumps({"text": text}))
            # 3. Stop frame — empty text signals end-of-input
            await ws.send(json.dumps({"text": ""}))

            chunks: List[bytes] = []
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                except (json.JSONDecodeError, TypeError):
                    continue
                # Accept common field name variants
                audio_b64 = (
                    msg.get("audio")
                    or msg.get("data")
                    or msg.get("audio_base64")
                )
                if audio_b64:
                    chunks.append(base64.b64decode(audio_b64))
                if msg.get("isFinal") or msg.get("is_final"):
                    break
            return chunks

    try:
        chunks = asyncio.run(_stream())
    except RuntimeError:
        # A running event loop exists (e.g., Jupyter, some async contexts).
        loop = asyncio.new_event_loop()
        try:
            chunks = loop.run_until_complete(_stream())
        finally:
            loop.close()

    if not chunks:
        raise RuntimeError(
            "Telnyx TTS returned no audio chunks. "
            "Verify TELNYX_API_KEY is valid and the voice name is correct."
        )

    with open(output_path, "wb") as fh:
        for chunk in chunks:
            fh.write(chunk)

    logger.info(
        "Telnyx TTS: wrote %d bytes to %s (voice=%s)",
        Path(output_path).stat().st_size,
        output_path,
        voice,
    )
    return output_path
