"""Pluggable text and speech providers."""

from podcast_factory.providers.base import SpeechProvider, TextProvider
from podcast_factory.providers.gemini import GeminiSpeechProvider, GeminiTextProvider

__all__ = [
    "SpeechProvider",
    "TextProvider",
    "GeminiSpeechProvider",
    "GeminiTextProvider",
    "get_text_provider",
    "get_speech_provider",
]


def get_text_provider(name: str, model: str) -> TextProvider:
    key = (name or "gemini").strip().lower()
    if key in {"gemini", "google", "google-gemini"}:
        return GeminiTextProvider(model=model)
    raise ValueError(
        f"Unknown text provider '{name}'. Built-in option: gemini. "
        "You can add another class that implements TextProvider."
    )


def get_speech_provider(name: str, model: str, fallbacks: list[str] | None = None) -> SpeechProvider:
    key = (name or "gemini").strip().lower()
    if key in {"gemini", "google", "google-gemini"}:
        return GeminiSpeechProvider(model=model, fallbacks=fallbacks or [])
    raise ValueError(
        f"Unknown speech provider '{name}'. Built-in option: gemini. "
        "You can add another class that implements SpeechProvider."
    )
