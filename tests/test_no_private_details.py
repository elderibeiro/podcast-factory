"""Guard the public tree against private contact details and family information."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "podcast_factory.egg-info",
}
TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".py", ".toml", ".txt", ".example", ".gitignore"}

# Built from parts so this test file does not itself contain the private strings.
FORBIDDEN_SNIPPETS = (
    "elder" + "+peep@",
    "mail." + "grokbot.com",
    "proton" + ".me",
    "proton" + "mail.com",
    "mary" + "stanton",
    "58" + "18",
    "by" + "ron st",
)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOWED_EMAIL_FRAGMENTS = (
    "users.noreply.github.com",
    "example.com",
    "example.org",
)


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {".gitignore", "LICENSE"}:
            continue
        if path.name == "test_no_private_details.py":
            continue
        yield path


def test_repo_has_no_personal_inboxes_or_home_address():
    violations: list[str] = []
    for path in _iter_text_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        lower = text.lower()
        rel = path.relative_to(ROOT)
        for snippet in FORBIDDEN_SNIPPETS:
            if snippet in lower:
                violations.append(f"{rel}: contains a private-detail marker")
        for match in EMAIL.findall(text):
            lowered = match.lower()
            if any(fragment in lowered for fragment in ALLOWED_EMAIL_FRAGMENTS):
                continue
            violations.append(f"{rel}: unexpected email {match}")
    assert violations == []
