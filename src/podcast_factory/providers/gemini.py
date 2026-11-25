"""Google Gemini text and TTS providers (free-tier defaults as of November 2026)."""

from __future__ import annotations

import base64
import os
import wave
from io import BytesIO
from pathlib import Path

from podcast_factory.providers.base import ProviderError, SpeechProvider, SpeechResult, TextProvider

# Official model IDs verified against https://ai.google.dev/gemini-api/docs/pricing
# on 2026-11-25. Free-tier rows listed "Free of charge" for these IDs.
DEFAULT_TEXT_MODEL = "gemini-3.5-flash-lite"
DEFAULT_TTS_MODEL = "gemini-3.8-flash-lite-tts"
DEFAULT_TTS_FALLBACKS = (
    "gemini-3.8-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-2.5-flash-preview-tts",
)

API_KEY_VARS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY")


def resolve_api_key() -> str:
    for name in API_KEY_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    raise ProviderError(
        "No Gemini API key found. Set GEMINI_API_KEY (or GOOGLE_API_KEY) "
        "in your environment or in a local .env file. See docs/gemini-api-key.md. "
        "Use --dry-run to render prompts without a key."
    )


def _client(api_key: str | None = None):
    try:
        from google import genai
    except ImportError as exc:
        raise ProviderError(
            "The google-genai package is required for live Gemini calls. "
            "Install dependencies with: pip install -e '.[dev]'"
        ) from exc
    return genai.Client(api_key=api_key or resolve_api_key())


def _extract_text(response: object) -> str:
    text = getattr(response, "text", None)
    if text:
        return str(text).strip()
    # Walk candidates/parts if the convenience property is empty.
    candidates = getattr(response, "candidates", None) or []
    chunks: list[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            value = getattr(part, "text", None)
            if value:
                chunks.append(str(value))
    if not chunks:
        raise ProviderError("Gemini returned no text. Try another model or inspect the prompt.")
    return "\n".join(chunks).strip()


class GeminiTextProvider(TextProvider):
    name = "gemini"

    def __init__(self, model: str = DEFAULT_TEXT_MODEL) -> None:
        self.model = model or DEFAULT_TEXT_MODEL

    def generate(self, prompt: str) -> str:
        client = _client()
        try:
            response = client.models.generate_content(model=self.model, contents=prompt)
        except Exception as exc:  # noqa: BLE001 — surface vendor errors cleanly
            raise ProviderError(f"Gemini text request failed ({self.model}): {exc}") from exc
        return _extract_text(response)


def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000, channels: int = 1, sample_width: int = 2) -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


def _as_wav(data: bytes, mime_type: str | None = None) -> tuple[bytes, str]:
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return data, "audio/wav"
    mime = (mime_type or "").lower()
    if "wav" in mime:
        return data, "audio/wav"
    # Gemini often returns raw PCM (audio/l16) at 24 kHz.
    return _pcm_to_wav(data), "audio/wav"


def _inline_audio_from_generate_content(response: object) -> tuple[bytes, str]:
    candidates = getattr(response, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        for part in parts:
            inline = getattr(part, "inline_data", None) or getattr(part, "inline_data".replace("_", ""), None)
            if inline is None:
                continue
            data = getattr(inline, "data", None)
            mime = getattr(inline, "mime_type", None) or getattr(inline, "mimeType", "") or "audio/wav"
            if not data:
                continue
            if isinstance(data, str):
                data = base64.b64decode(data)
            return bytes(data), str(mime)
    raise ProviderError("Gemini TTS returned no audio data.")


def _audio_from_interaction(interaction: object) -> tuple[bytes, str]:
    output_audio = getattr(interaction, "output_audio", None)
    if output_audio is not None:
        data = getattr(output_audio, "data", None)
        mime = getattr(output_audio, "mime_type", None) or "audio/wav"
        if data:
            if isinstance(data, str):
                data = base64.b64decode(data)
            return bytes(data), str(mime)
    # Fall back to walking steps/content in case the convenience property is absent.
    steps = getattr(interaction, "steps", None) or []
    for step in steps:
        contents = getattr(step, "content", None) or []
        if not isinstance(contents, list):
            contents = [contents]
        for item in contents:
            data = getattr(item, "data", None)
            mime = getattr(item, "mime_type", None) or getattr(item, "mimeType", "") or "audio/wav"
            if data:
                if isinstance(data, str):
                    data = base64.b64decode(data)
                return bytes(data), str(mime)
    raise ProviderError("Gemini TTS interaction returned no audio data.")


class GeminiSpeechProvider(SpeechProvider):
    """Gemini TTS with official 3.8 models first, then older preview TTS models."""

    name = "gemini"

    def __init__(self, model: str = DEFAULT_TTS_MODEL, fallbacks: list[str] | None = None) -> None:
        self.model = model or DEFAULT_TTS_MODEL
        self.fallbacks = list(fallbacks or DEFAULT_TTS_FALLBACKS)

    def synthesize(self, text: str, voice: str, style: str = "") -> SpeechResult:
        client = _client()
        errors: list[str] = []
        for model in [self.model, *[m for m in self.fallbacks if m != self.model]]:
            try:
                audio, mime, used = self._synthesize_with(client, model, text, voice, style)
                wav, mime = _as_wav(audio, mime)
                note = "" if used == self.model else f"Used fallback model {used} after {self.model} failed."
                return SpeechResult(audio=wav, mime_type=mime, model=used, voice=voice, notes=note)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{model}: {exc}")
        raise ProviderError(
            "All Gemini TTS models failed. Last errors:\n- " + "\n- ".join(errors)
        )

    def _synthesize_with(self, client: object, model: str, text: str, voice: str, style: str) -> tuple[bytes, str, str]:
        # Gemini 3.8 TTS uses the Interactions API (v1beta). Older preview TTS
        # models still accept generate_content with AUDIO response modality.
        if "3.8" in model or model.endswith("-tts") and not model.startswith("gemini-2."):
            try:
                return self._via_interactions(client, model, text, voice, style), "audio/wav", model
            except Exception:
                # Some SDK versions may only expose generate_content; try it next.
                try:
                    data, mime = self._via_generate_content(client, model, text, voice)
                    return data, mime, model
                except Exception as exc:
                    raise exc
        data, mime = self._via_generate_content(client, model, text, voice)
        return data, mime, model

    def _via_interactions(self, client: object, model: str, text: str, voice: str, style: str) -> bytes:
        interaction_client = getattr(client, "interactions", None)
        if interaction_client is None:
            raise ProviderError("This google-genai SDK build has no interactions API.")
        style_text = style or "warm, clear, and neighborly, like a local weekly briefing"
        # Documented shape: https://ai.google.dev/gemini-api/docs/speech-generation
        try:
            interaction = interaction_client.create(
                model=model,
                input=[
                    {
                        "type": "user_input",
                        "content": [
                            {
                                "type": "text",
                                "text": text,
                                "annotations": [{"type": "speech_metadata", "style": style_text}],
                            }
                        ],
                    }
                ],
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voice}]},
            )
        except TypeError:
            # Older keyword names, if the SDK is mid-migration.
            interaction = interaction_client.create(
                model=model,
                input=text,
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voice}]},
            )
        data, _mime = _audio_from_interaction(interaction)
        return data

    def _via_generate_content(self, client: object, model: str, text: str, voice: str) -> tuple[bytes, str]:
        from google.genai import types

        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        )
        response = client.models.generate_content(model=model, contents=text, config=config)
        return _inline_audio_from_generate_content(response)


def write_wav(path: Path, audio: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(audio)
    return path
