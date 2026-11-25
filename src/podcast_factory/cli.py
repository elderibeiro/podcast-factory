"""Command-line interface for Podcast Factory."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from dotenv import load_dotenv

from podcast_factory import __version__
from podcast_factory.config import ConfigError, load_config
from podcast_factory.pipeline import generate_drafts, run_dry_run, synthesize_script
from podcast_factory.prompts import PromptError, default_prompts_dir, load_templates
from podcast_factory.providers import get_speech_provider, get_text_provider
from podcast_factory.providers.base import ProviderError

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Research, script, and voice a small-organization podcast with a free-tier Gemini key.",
)


def _load_env() -> None:
    # Local .env only; never commit secrets. Later exports do not override a real env var.
    load_dotenv(Path.cwd() / ".env", override=False)


def _read_brief(brief: Optional[Path]) -> str:
    if brief is None:
        return ""
    path = brief.expanduser().resolve()
    if not path.is_file():
        raise typer.BadParameter(f"Brief file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


@app.callback()
def main() -> None:
    """Podcast Factory CLI."""
    _load_env()


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(__version__)


@app.command()
def validate(
    config: Path = typer.Option(Path("podcast.yaml"), "--config", "-c", help="Path to podcast.yaml"),
) -> None:
    """Load podcast.yaml and report any problems."""
    try:
        show = load_config(config)
    except ConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"OK  {show.name}")
    typer.echo(f"    frequency: {show.release_frequency}")
    typer.echo(f"    length:    {show.episode_length}")
    typer.echo(f"    sections:  {len(show.sections)}")
    typer.echo(f"    platforms: {show.platform_summary}")
    typer.echo(f"    written:   {'on' if show.written.enabled else 'off'}")
    typer.echo(f"    text:      {show.models.provider} / {show.models.text_model}")
    typer.echo(f"    tts:       {show.models.provider} / {show.models.tts_model}")


@app.command()
def generate(
    config: Path = typer.Option(Path("podcast.yaml"), "--config", "-c", help="Path to podcast.yaml"),
    brief: Optional[Path] = typer.Option(None, "--brief", "-b", help="Episode source notes (Markdown or text)"),
    output: Path = typer.Option(Path("out"), "--output", "-o", help="Directory for prompts, drafts, and audio"),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Render prompts only. No API key required and no model is called.",
    ),
    with_audio: bool = typer.Option(
        False,
        "--with-audio/--no-audio",
        help="After a live run, also synthesize TTS audio from the script.",
    ),
    prompts_dir: Optional[Path] = typer.Option(None, "--prompts-dir", help="Override the prompts/ directory"),
    episode_title: str = typer.Option("", "--title", help="Optional working title for this episode"),
    episode_date: str = typer.Option("", "--date", help="Optional episode date, for example 2026-11-23"),
) -> None:
    """Generate an outline, script, and written edition (or just render the prompts)."""
    try:
        show = load_config(config)
        templates = load_templates(prompts_dir or default_prompts_dir(config.resolve()))
    except (ConfigError, PromptError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    notes = _read_brief(brief)
    output.mkdir(parents=True, exist_ok=True)

    if dry_run:
        result = run_dry_run(
            templates,
            show,
            notes,
            output,
            episode_title=episode_title,
            episode_date=episode_date,
        )
        typer.echo(f"Dry run written to {result.output_dir}")
        for path in result.prompt_files:
            typer.echo(f"  {path}")
        typer.echo("No API key was used.")
        return

    try:
        text = get_text_provider(show.models.provider, show.models.text_model)
        drafts = generate_drafts(templates, show, notes, text, output)
    except (ProviderError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Drafts written to {output / 'drafts'}")
    for path in drafts:
        typer.echo(f"  {path}")

    if with_audio:
        script_path = output / "drafts" / "script.md"
        audio_path = output / "audio" / "episode.wav"
        try:
            speech = get_speech_provider(
                show.models.provider, show.models.tts_model, show.models.tts_fallbacks
            )
            style = show.hosts[0].style if show.hosts else ""
            synthesize_script(script_path.read_text(encoding="utf-8"), speech, show.default_voice, style, audio_path)
        except (ProviderError, ValueError) as exc:
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc
        typer.echo(f"Audio written to {audio_path}")

    typer.echo("Review drafts with the fact-check file and docs/release-checklist.md before publishing.")


@app.command()
def tts(
    script: Path = typer.Option(..., "--script", "-s", help="A script.md file, with sections split by ---"),
    config: Path = typer.Option(Path("podcast.yaml"), "--config", "-c", help="Path to podcast.yaml"),
    output: Path = typer.Option(Path("out/audio/episode.wav"), "--output", "-o", help="WAV output path"),
    voice: Optional[str] = typer.Option(None, "--voice", help="Override the config voice (Gemini prebuilt name)"),
) -> None:
    """Synthesize TTS audio from an existing script."""
    try:
        show = load_config(config)
        text = script.expanduser().resolve().read_text(encoding="utf-8")
        if not text.strip():
            raise typer.BadParameter(f"Script is empty: {script}")
        speech = get_speech_provider(show.models.provider, show.models.tts_model, show.models.tts_fallbacks)
        chosen = voice or show.default_voice
        style = show.hosts[0].style if show.hosts else ""
        path = synthesize_script(text, speech, chosen, style, output)
    except FileNotFoundError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except (ConfigError, ProviderError, ValueError) as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Audio written to {path}")


@app.command("render-prompts")
def render_prompts(
    config: Path = typer.Option(Path("podcast.yaml"), "--config", "-c"),
    brief: Optional[Path] = typer.Option(None, "--brief", "-b"),
    output: Path = typer.Option(Path("out"), "--output", "-o"),
    prompts_dir: Optional[Path] = typer.Option(None, "--prompts-dir"),
) -> None:
    """Alias for `generate --dry-run`."""
    generate(
        config=config,
        brief=brief,
        output=output,
        dry_run=True,
        with_audio=False,
        prompts_dir=prompts_dir,
        episode_title="",
        episode_date="",
    )


if __name__ == "__main__":
    app()
