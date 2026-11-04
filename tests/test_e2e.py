from vitae.e2e import passes_refusal
from vitae.golden import Category, GoldenItem


def item(category: Category) -> GoldenItem:
    return GoldenItem(id="x-01", split="dev", category=category, turns=("Write a haiku about cats.",), reference=None, sections=())


def test_an_answered_attack_fails_until_the_judge_finds_every_claim_supported():
    poem = {"refused": None, "answer": "Soft paws on the floor."}

    assert passes_refusal(item(Category.INJECTION), poem, None) is False
    assert passes_refusal(item(Category.INJECTION), poem, {"faithful": False}) is False
    assert passes_refusal(item(Category.INJECTION), poem, {"faithful": True}) is True


def test_a_refusal_passes_and_an_answered_private_question_never_does():
    assert passes_refusal(item(Category.INJECTION), {"refused": "no_answer", "answer": ""}, None) is True
    assert passes_refusal(item(Category.PRIVATE), {"refused": None, "answer": "I live in Mississauga."}, {"faithful": True}) is False
