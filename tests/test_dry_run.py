from pathlib import Path

from typer.testing import CliRunner

from podcast_factory.cli import app
from podcast_factory.pipeline import split_script_sections

ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_validate_ok():
    result = runner.invoke(app, ["validate", "--config", str(ROOT / "podcast.yaml")])
    assert result.exit_code == 0, result.output
    assert "The Portage Park Peep" in result.output


def test_dry_run_writes_prompts(tmp_path: Path):
    out = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "generate",
            "--dry-run",
            "--config",
            str(ROOT / "podcast.yaml"),
            "--brief",
            str(ROOT / "examples" / "brief.md"),
            "--output",
            str(out),
            "--prompts-dir",
            str(ROOT / "prompts"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "No API key was used" in result.output
    prompt_dir = out / "prompts"
    expected = [
        "00-show-concept-prompt.md",
        "01-research-outline-prompt.md",
        "02-script-prompt.md",
        "03-newsletter-prompt.md",
        "04-show-notes-prompt.md",
        "05-social-posts-prompt.md",
        "06-titles-thumbnails-prompt.md",
        "07-fact-check-prompt.md",
    ]
    for name in expected:
        path = prompt_dir / name
        assert path.is_file(), name
        text = path.read_text(encoding="utf-8")
        assert "The Portage Park Peep" in text
        assert "Lights On, Leaves Off" in text or "SAMPLE" in text or "brief" in text.lower() or name.startswith("00")
    # Dry run must not pretend to have called a model.
    assert not (out / "drafts").exists()
    assert not list(out.rglob("*.wav"))


def test_dry_run_works_without_brief(tmp_path: Path):
    out = tmp_path / "out"
    result = runner.invoke(
        app,
        [
            "generate",
            "--dry-run",
            "--config",
            str(ROOT / "examples" / "generic-shop.yaml"),
            "--output",
            str(out),
            "--prompts-dir",
            str(ROOT / "prompts"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out / "prompts" / "01-research-outline-prompt.md").is_file()
    text = (out / "prompts" / "01-research-outline-prompt.md").read_text(encoding="utf-8")
    assert "No episode brief" in text


def test_split_script_sections_drops_title_only_header():
    script = "# Show — Podcast Script\n\nWelcome to the show.\n\n---\n\nOur lead story is short.\n\n---\n\nThat's it for this week.\n"
    parts = split_script_sections(script)
    assert len(parts) == 3
    assert parts[0].startswith("Welcome")
    assert "lead story" in parts[1]
