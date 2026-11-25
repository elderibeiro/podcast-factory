"""Load Markdown prompt templates and fill them from a show config."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

PROMPT_FILES: tuple[tuple[str, str], ...] = (
    ("show_concept", "01-show-concept.md"),
    ("research_outline", "02-research-outline.md"),
    ("script", "03-script-section.md"),
    ("newsletter", "04-blog-newsletter.md"),
    ("show_notes", "05-show-notes.md"),
    ("social", "06-social-posts.md"),
    ("titles", "07-titles-thumbnails.md"),
    ("fact_check", "08-fact-check-safety.md"),
)

# Placeholders look like {show_name}. Double braces escape a literal brace.
PLACEHOLDER = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")


class PromptError(ValueError):
    """A prompt template is missing or could not be rendered."""


@dataclass(frozen=True)
class PromptTemplate:
    key: str
    name: str
    path: Path
    body: str

    def render(self, variables: dict[str, str]) -> str:
        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            if key not in variables:
                return match.group(0)
            return str(variables[key])

        return PLACEHOLDER.sub(replace, self.body)


def default_prompts_dir(start: Path | None = None) -> Path:
    """Find the repo's prompts/ directory, walking up from start or cwd."""
    candidates: list[Path] = []
    if start is not None:
        candidates.append(start if start.is_dir() else start.parent)
    candidates.append(Path.cwd())
    # Installed package is at src/podcast_factory; the repo root is two parents up in dev.
    candidates.append(Path(__file__).resolve().parents[2])
    seen: set[Path] = set()
    for base in candidates:
        for directory in [base, *base.parents]:
            resolved = directory.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            prompts = resolved / "prompts"
            if (prompts / "02-research-outline.md").is_file():
                return prompts
    raise PromptError(
        "Could not find a prompts/ directory. Pass --prompts-dir or run from the repo root."
    )


def load_templates(prompts_dir: Path | None = None) -> dict[str, PromptTemplate]:
    directory = prompts_dir or default_prompts_dir()
    if not directory.is_dir():
        raise PromptError(f"Prompts directory not found: {directory}")
    templates: dict[str, PromptTemplate] = {}
    for key, filename in PROMPT_FILES:
        path = directory / filename
        if not path.is_file():
            raise PromptError(f"Missing prompt template: {path}")
        templates[key] = PromptTemplate(
            key=key,
            name=filename,
            path=path,
            body=path.read_text(encoding="utf-8"),
        )
    return templates


def render_all(
    templates: dict[str, PromptTemplate],
    variables: dict[str, str],
    include_newsletter: bool = True,
) -> dict[str, str]:
    rendered: dict[str, str] = {}
    for key, template in templates.items():
        if key == "newsletter" and not include_newsletter:
            continue
        rendered[key] = template.render(variables)
    return rendered
