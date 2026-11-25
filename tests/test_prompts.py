from pathlib import Path

from podcast_factory.config import load_config
from podcast_factory.prompts import load_templates, render_all

ROOT = Path(__file__).resolve().parents[1]


def test_all_prompt_templates_exist():
    templates = load_templates(ROOT / "prompts")
    assert set(templates) == {
        "show_concept",
        "research_outline",
        "script",
        "newsletter",
        "show_notes",
        "social",
        "titles",
        "fact_check",
    }


def test_render_substitutes_show_fields():
    show = load_config(ROOT / "podcast.yaml")
    templates = load_templates(ROOT / "prompts")
    brief = "SAMPLE: lights go on Saturday at five p.m., source: association flyer."
    rendered = render_all(templates, show.as_prompt_vars({"brief": brief}))
    script = rendered["script"]
    assert "The Portage Park Peep" in script
    assert "Commerce Corner" in script
    assert brief in rendered["research_outline"]
    assert "{show_name}" not in script
    assert "{brief}" not in rendered["research_outline"]


def test_newsletter_can_be_skipped():
    show = load_config(ROOT / "podcast.yaml")
    templates = load_templates(ROOT / "prompts")
    rendered = render_all(templates, show.as_prompt_vars(), include_newsletter=False)
    assert "newsletter" not in rendered
    assert "script" in rendered
