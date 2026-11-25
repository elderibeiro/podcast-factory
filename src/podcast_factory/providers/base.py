"""Provider interfaces. Swap Gemini for another vendor without changing the CLI."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


class ProviderError(RuntimeError):
    """A text or speech provider failed."""


@dataclass
class SpeechResult:
    audio: bytes
    mime_type: str
    model: str
    voice: str
    notes: str = ""


class TextProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Return the model’s text completion for a single prompt."""


class SpeechProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def synthesize(self, text: str, voice: str, style: str = "") -> SpeechResult:
        """Return audio bytes for the given narration text."""
