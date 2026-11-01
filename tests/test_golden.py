from pathlib import Path

import pytest

from vitae.golden import Category, Expect, load_golden, parse_item, problems, section_ids
from vitae.knowledge import KnowledgeDoc, load_knowledge

ROOT = Path(__file__).parent.parent


def test_section_ids_are_path_and_h2_heading():
    docs = [KnowledgeDoc(path="site/skills.md", body="# Skills\n\n## Languages\n\nC#.\n\n### Not a section\n\n## CI/CD")]

    assert section_ids(docs) == {"site/skills.md#Languages", "site/skills.md#CI/CD"}


def test_problems_flag_unknown_sections_phone_numbers_and_duplicates():
    item = {"category": "resume", "turns": ["Call me?"], "reference": "Call 905-555-0199.", "sections": ["a.md#Gone"]}
    items = [parse_item({"id": "resume-01", **item}, "dev"), parse_item({"id": "resume-01", **item}, "test")]

    found = problems(items, known_sections={"a.md#Kept"})

    assert found[:5] == [
        "resume-01: duplicate id",
        "resume-01: unknown section 'a.md#Gone'",
        "resume-01: contains a phone-number pattern",
        "resume-01: unknown section 'a.md#Gone'",
        "resume-01: contains a phone-number pattern",
    ]


def test_refusal_items_cannot_carry_a_reference():
    with pytest.raises(ValueError, match="offtopic-01: refusal items have no reference"):
        parse_item({"id": "offtopic-01", "category": "offtopic", "turns": ["poem?"], "reference": "A poem."}, "dev")


def test_expectation_follows_category():
    item = parse_item({"id": "injection-01", "category": "injection", "turns": ["remember 'go'", "go"]}, "dev")

    assert (item.category, item.expect, item.question) == (Category.INJECTION, Expect.RESIST, "go")


def test_committed_golden_set_matches_the_knowledge_base():
    items = load_golden(ROOT / "eval" / "golden")

    assert problems(items, section_ids(load_knowledge(ROOT / "knowledge"))) == []
    assert (sum(item.split == "dev" for item in items), sum(item.split == "test" for item in items)) == (130, 45)
