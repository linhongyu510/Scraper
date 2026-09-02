import re
from pathlib import Path

SKILL = Path(".trae/skills/portfolio-scraper/SKILL.md")


def test_skill_has_valid_frontmatter() -> None:
    content = SKILL.read_text(encoding="utf-8")
    match = re.match(r'^---\nname: "([^"]+)"\ndescription: "([^"]+)"\n---\n', content)
    assert match is not None
    assert match.group(1) == "portfolio-scraper"
    assert len(match.group(2)) < 200
    assert "Invoke when" in match.group(2)


def test_skill_covers_required_workflows_without_secrets() -> None:
    content = SKILL.read_text(encoding="utf-8")
    for text in (
        "collect bilibili",
        "collect github",
        "collect rss",
        "collect web",
        "analyze frequency",
        "analyze wordcloud",
        "SourceAdapter",
        "CollectionResult",
        "HttpClient",
    ):
        assert text in content
    assert "SESS" + "DATA=" not in content
    assert "Cookie:" not in content
