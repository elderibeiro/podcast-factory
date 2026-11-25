from pathlib import Path

import pytest

from podcast_factory.config import ConfigError, load_config

ROOT = Path(__file__).resolve().parents[1]


def test_example_peep_config_loads():
    show = load_config(ROOT / "podcast.yaml")
    assert show.name == "The Portage Park Peep"
    assert show.written.enabled
    assert show.typical_minutes == 5
    assert show.release_frequency.lower().startswith("weekly")
    assert {s.id for s in show.sections} >= {"welcome", "lead", "snapshot", "commerce", "signoff"}
    assert show.models.text_model == "gemini-3.5-flash-lite"
    assert show.models.tts_model == "gemini-3.8-flash-lite-tts"
    assert show.platforms.spotify and show.platforms.apple_podcasts
    assert "Kore" in show.host_summary
    assert "elder+" not in show.signoff.lower()


def test_generic_shop_config_loads():
    show = load_config(ROOT / "examples" / "generic-shop.yaml")
    assert show.name == "Main Street Weekly"
    assert show.models.provider == "gemini"


def test_missing_required_field_raises(tmp_path: Path):
    path = tmp_path / "podcast.yaml"
    path.write_text("show:\n  name: Only a name\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="missing required"):
        load_config(path)


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "nope.yaml")
