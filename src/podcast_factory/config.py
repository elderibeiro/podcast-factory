"""Load and validate a Podcast Factory show config (podcast.yaml)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REQUIRED_TOP_LEVEL = ("show",)


class ConfigError(ValueError):
    """The show config is missing required fields or has invalid values."""


def _require(data: dict[str, Any], *keys: str, ctx: str) -> None:
    missing = [k for k in keys if not str(data.get(k, "")).strip()]
    if missing:
        raise ConfigError(f"{ctx} is missing required field(s): {', '.join(missing)}")


@dataclass
class Host:
    name: str
    role: str = "narrator"
    voice: str = "Kore"
    style: str = "warm, clear, neighborly"


@dataclass
class Section:
    id: str
    name: str
    description: str = ""
    required: bool = True
    typical_seconds: int | None = None


@dataclass
class Platforms:
    rss: bool = True
    spotify: bool = True
    apple_podcasts: bool = True
    amazon_music: bool = True
    youtube: bool = True


@dataclass
class WrittenEdition:
    enabled: bool = True
    formats: list[str] = field(default_factory=lambda: ["newsletter", "blog"])


@dataclass
class Models:
    provider: str = "gemini"
    text_model: str = "gemini-3.5-flash-lite"
    tts_model: str = "gemini-3.8-flash-lite-tts"
    tts_fallbacks: list[str] = field(
        default_factory=lambda: [
            "gemini-3.8-flash-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-flash-preview-tts",
        ]
    )


@dataclass
class ShowConfig:
    """A filled-in show definition, plus optional model and path settings."""

    path: Path
    name: str
    tagline: str
    niche: str
    target_audience: str
    tone: str
    language: str
    release_frequency: str
    episode_length: str
    typical_minutes: int
    signoff: str
    hosts: list[Host]
    sections: list[Section]
    platforms: Platforms
    written: WrittenEdition
    sources: list[str]
    news_inputs: list[str]
    models: Models
    raw: dict[str, Any]

    @property
    def default_voice(self) -> str:
        return self.hosts[0].voice if self.hosts else "Kore"

    @property
    def host_summary(self) -> str:
        if not self.hosts:
            return "A single unnamed narrator."
        parts = []
        for h in self.hosts:
            bits = [h.name, f"role: {h.role}", f"voice: {h.voice}"]
            if h.style:
                bits.append(f"style: {h.style}")
            parts.append(", ".join(bits))
        return "; ".join(parts)

    @property
    def section_summary(self) -> str:
        lines = []
        for s in self.sections:
            flag = "required" if s.required else "optional / rotating"
            length = f", ~{s.typical_seconds}s" if s.typical_seconds else ""
            desc = f" — {s.description}" if s.description else ""
            lines.append(f"- {s.name} ({s.id}, {flag}{length}){desc}")
        return "\n".join(lines)

    @property
    def platform_summary(self) -> str:
        names = []
        if self.platforms.rss:
            names.append("RSS")
        if self.platforms.spotify:
            names.append("Spotify for Creators")
        if self.platforms.apple_podcasts:
            names.append("Apple Podcasts")
        if self.platforms.amazon_music:
            names.append("Amazon Music / Audible")
        if self.platforms.youtube:
            names.append("YouTube podcasts")
        return ", ".join(names) if names else "none listed"

    @property
    def source_summary(self) -> str:
        return "\n".join(f"- {s}" for s in self.sources) if self.sources else "- (none listed)"

    @property
    def news_input_summary(self) -> str:
        return "\n".join(f"- {s}" for s in self.news_inputs) if self.news_inputs else "- (none listed)"

    def as_prompt_vars(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Flat string map used to fill prompt templates."""
        written = "on" if self.written.enabled else "off"
        if self.written.enabled and self.written.formats:
            written += " (" + ", ".join(self.written.formats) + ")"
        vars_: dict[str, str] = {
            "show_name": self.name,
            "tagline": self.tagline,
            "niche": self.niche,
            "target_audience": self.target_audience,
            "tone": self.tone,
            "language": self.language,
            "release_frequency": self.release_frequency,
            "episode_length": self.episode_length,
            "typical_minutes": str(self.typical_minutes),
            "signoff": self.signoff,
            "hosts": self.host_summary,
            "default_voice": self.default_voice,
            "sections": self.section_summary,
            "platforms": self.platform_summary,
            "written_edition": written,
            "sources": self.source_summary,
            "news_inputs": self.news_input_summary,
            "text_model": self.models.text_model,
            "tts_model": self.models.tts_model,
            "provider": self.models.provider,
            "brief": "",
            "outline": "",
            "script": "",
            "episode_title": "",
            "episode_date": "",
        }
        if extra:
            vars_.update({k: str(v) for k, v in extra.items()})
        return vars_


def _parse_hosts(raw: Any) -> list[Host]:
    if not raw:
        return [Host(name="Narrator", role="narrator", voice="Kore")]
    hosts: list[Host] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("name"):
            raise ConfigError("Each hosts entry needs a name.")
        hosts.append(
            Host(
                name=str(item["name"]),
                role=str(item.get("role", "narrator")),
                voice=str(item.get("voice", "Kore")),
                style=str(item.get("style", "warm, clear, neighborly")),
            )
        )
    return hosts


def _parse_sections(raw: Any) -> list[Section]:
    if not raw:
        raise ConfigError("show.sections must list at least one segment.")
    sections: list[Section] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("name"):
            raise ConfigError("Each sections entry needs a name.")
        name = str(item["name"])
        sid = str(item.get("id") or name.lower().replace(" ", "-").replace("&", "and"))
        sections.append(
            Section(
                id=sid,
                name=name,
                description=str(item.get("description", "")),
                required=bool(item.get("required", True)),
                typical_seconds=int(item["typical_seconds"]) if item.get("typical_seconds") else None,
            )
        )
    return sections


def load_config(path: Path) -> ShowConfig:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("podcast.yaml must be a mapping.")
    show = data.get("show")
    if not isinstance(show, dict):
        raise ConfigError("podcast.yaml must have a top-level 'show' mapping.")
    _require(
        show,
        "name",
        "niche",
        "target_audience",
        "tone",
        "language",
        "release_frequency",
        "episode_length",
        ctx="show",
    )

    platforms_raw = show.get("platforms") or {}
    if not isinstance(platforms_raw, dict):
        raise ConfigError("show.platforms must be a mapping of platform names to true/false.")
    platforms = Platforms(
        rss=bool(platforms_raw.get("rss", True)),
        spotify=bool(platforms_raw.get("spotify", platforms_raw.get("spotify_for_creators", True))),
        apple_podcasts=bool(platforms_raw.get("apple_podcasts", platforms_raw.get("apple", True))),
        amazon_music=bool(platforms_raw.get("amazon_music", platforms_raw.get("amazon", True))),
        youtube=bool(platforms_raw.get("youtube", True)),
    )

    written_raw = show.get("written") or show.get("newsletter") or show.get("blog") or {}
    if isinstance(written_raw, bool):
        written = WrittenEdition(enabled=written_raw)
    elif isinstance(written_raw, dict):
        formats = written_raw.get("formats") or ["newsletter", "blog"]
        if isinstance(formats, str):
            formats = [formats]
        written = WrittenEdition(enabled=bool(written_raw.get("enabled", True)), formats=list(formats))
    else:
        raise ConfigError("show.written must be a boolean or a mapping.")

    models_raw = data.get("models") or {}
    if not isinstance(models_raw, dict):
        raise ConfigError("models must be a mapping if present.")
    fallbacks = models_raw.get(
        "tts_fallbacks",
        [
            "gemini-3.8-flash-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-flash-preview-tts",
        ],
    )
    models = Models(
        provider=str(models_raw.get("provider", "gemini")),
        text_model=str(models_raw.get("text_model", "gemini-3.5-flash-lite")),
        tts_model=str(models_raw.get("tts_model", "gemini-3.8-flash-lite-tts")),
        tts_fallbacks=list(fallbacks),
    )

    sources = show.get("sources") or []
    news_inputs = show.get("news_inputs") or show.get("inputs") or []
    if isinstance(sources, str):
        sources = [sources]
    if isinstance(news_inputs, str):
        news_inputs = [news_inputs]

    typical = show.get("typical_minutes")
    if typical is None:
        # Best-effort parse of values like "about 5 minutes".
        digits = "".join(ch if ch.isdigit() else " " for ch in str(show["episode_length"]))
        parts = [int(p) for p in digits.split() if p]
        typical = parts[0] if parts else 5

    return ShowConfig(
        path=path,
        name=str(show["name"]),
        tagline=str(show.get("tagline", "")),
        niche=str(show["niche"]),
        target_audience=str(show["target_audience"]),
        tone=str(show["tone"]),
        language=str(show["language"]),
        release_frequency=str(show["release_frequency"]),
        episode_length=str(show["episode_length"]),
        typical_minutes=int(typical),
        signoff=str(show.get("signoff", f"This has been {show['name']}. See you next time.")),
        hosts=_parse_hosts(show.get("hosts")),
        sections=_parse_sections(show.get("sections")),
        platforms=platforms,
        written=written,
        sources=[str(s) for s in sources],
        news_inputs=[str(s) for s in news_inputs],
        models=models,
        raw=data,
    )
