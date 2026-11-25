"""Turn a show config + episode brief into prompts, drafts, and optional audio."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from podcast_factory.config import ShowConfig
from podcast_factory.prompts import PromptTemplate, render_all
from podcast_factory.providers.base import SpeechProvider, TextProvider
from podcast_factory.providers.gemini import write_wav

OUTPUT_NAMES = {
    "show_concept": "00-show-concept-prompt.md",
    "research_outline": "01-research-outline-prompt.md",
    "script": "02-script-prompt.md",
    "newsletter": "03-newsletter-prompt.md",
    "show_notes": "04-show-notes-prompt.md",
    "social": "05-social-posts-prompt.md",
    "titles": "06-titles-thumbnails-prompt.md",
    "fact_check": "07-fact-check-prompt.md",
}

DRAFT_NAMES = {
    "research_outline": "outline.md",
    "script": "script.md",
    "newsletter": "newsletter.md",
    "show_notes": "show-notes.md",
    "social": "social-posts.md",
    "titles": "titles-and-thumbnails.md",
    "fact_check": "fact-check.md",
}

# The live Peep script splits sections with a markdown horizontal rule on its own line.
SECTION_SPLIT = re.compile(r"\n---\n")


@dataclass
class PipelineResult:
    output_dir: Path
    dry_run: bool
    prompt_files: list[Path]
    draft_files: list[Path]
    audio_file: Path | None = None
    notes: list[str] | None = None


def split_script_sections(script: str) -> list[str]:
    """Split a script into spoken sections, stripping a leading markdown title."""
    parts = [p.strip() for p in SECTION_SPLIT.split(script) if p.strip()]
    if not parts:
        return [script.strip()]
    # Real scripts start with a title line, then the welcome in the same block.
    first_lines = parts[0].splitlines()
    if first_lines and first_lines[0].lstrip().startswith("#"):
        rest = "\n".join(first_lines[1:]).strip()
        if rest:
            parts[0] = rest
        elif len(parts) > 1:
            parts = parts[1:]
    return parts


def _wav_frames(data: bytes) -> tuple[bytes, int, int, int]:
    import wave
    from io import BytesIO

    with wave.open(BytesIO(data), "rb") as wav:
        return wav.readframes(wav.getnframes()), wav.getframerate(), wav.getnchannels(), wav.getsampwidth()


def concat_wavs(chunks: Iterable[bytes], gap_seconds: float = 0.6) -> bytes:
    import wave
    from io import BytesIO

    items = list(chunks)
    if not items:
        raise ValueError("No audio chunks to concatenate.")
    frames, rate, channels, width = _wav_frames(items[0])
    gap = b"\x00" * int(rate * gap_seconds) * channels * width
    body = bytearray(frames)
    for chunk in items[1:]:
        more, more_rate, more_channels, more_width = _wav_frames(chunk)
        if (more_rate, more_channels, more_width) != (rate, channels, width):
            # Still append; most Gemini voices share 24 kHz mono PCM. A mismatch
            # is rare enough that we warn by writing the later chunk as-is only
            # when params match; otherwise skip the gap math and just extend.
            if more_width == width and more_channels == channels:
                body.extend(gap)
                body.extend(more)
            continue
        body.extend(gap)
        body.extend(more)
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(width)
        wav.setframerate(rate)
        wav.writeframes(bytes(body))
    return buffer.getvalue()


def write_prompts(output_dir: Path, rendered: dict[str, str]) -> list[Path]:
    prompts_dir = output_dir / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for key, body in rendered.items():
        path = prompts_dir / OUTPUT_NAMES.get(key, f"{key}.md")
        path.write_text(body.rstrip() + "\n", encoding="utf-8")
        written.append(path)
    return written


def generate_drafts(
    templates: dict[str, PromptTemplate],
    config: ShowConfig,
    brief: str,
    text: TextProvider,
    output_dir: Path,
) -> list[Path]:
    drafts_dir = output_dir / "drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    extra = {"brief": brief}

    def run(key: str, extra_vars: dict[str, str]) -> str:
        template = templates[key]
        prompt = template.render(config.as_prompt_vars(extra_vars))
        result = text.generate(prompt)
        path = drafts_dir / DRAFT_NAMES[key]
        path.write_text(result.rstrip() + "\n", encoding="utf-8")
        written.append(path)
        return result

    outline = run("research_outline", extra)
    extra["outline"] = outline
    script = run("script", extra)
    extra["script"] = script
    if config.written.enabled:
        run("newsletter", extra)
    run("show_notes", extra)
    run("social", extra)
    run("titles", extra)
    run("fact_check", extra)
    return written


def synthesize_script(
    script: str,
    speech: SpeechProvider,
    voice: str,
    style: str,
    output_path: Path,
) -> Path:
    sections = split_script_sections(script)
    chunks: list[bytes] = []
    notes: list[str] = []
    for section in sections:
        # Keep each request short, the way a weekly briefing is usually voiced.
        result = speech.synthesize(section.replace("\n", " "), voice=voice, style=style)
        chunks.append(result.audio)
        if result.notes:
            notes.append(result.notes)
    audio = concat_wavs(chunks) if len(chunks) > 1 else chunks[0]
    write_wav(output_path, audio)
    if notes:
        output_path.with_suffix(".txt").write_text("\n".join(dict.fromkeys(notes)) + "\n", encoding="utf-8")
    return output_path


def run_dry_run(
    templates: dict[str, PromptTemplate],
    config: ShowConfig,
    brief: str,
    output_dir: Path,
    episode_title: str = "",
    episode_date: str = "",
) -> PipelineResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    variables = config.as_prompt_vars(
        {
            "brief": brief or "(No episode brief supplied. Add source notes before a live run.)",
            "episode_title": episode_title,
            "episode_date": episode_date,
        }
    )
    rendered = render_all(templates, variables, include_newsletter=config.written.enabled)
    prompt_files = write_prompts(output_dir, rendered)
    readme = output_dir / "README.md"
    names = "\n".join(f"- `{p.relative_to(output_dir)}`" for p in prompt_files)
    readme.write_text(
        "\n".join(
            [
                f"# Dry run for {config.name}",
                "",
                "These files are the prompts Podcast Factory would send to the language model.",
                "No API key was used. Review them, then run without `--dry-run` to generate drafts.",
                "",
                "## Rendered prompts",
                names,
                "",
                "Live generation also writes `drafts/outline.md`, `drafts/script.md`"
                + (", `drafts/newsletter.md`" if config.written.enabled else "")
                + ", show notes, social posts, titles, and a fact-check pass.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return PipelineResult(
        output_dir=output_dir,
        dry_run=True,
        prompt_files=prompt_files,
        draft_files=[],
        notes=["Dry run only. Prompts were rendered; no model was called."],
    )
