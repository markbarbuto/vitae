import json
import re
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from vitae.knowledge import KnowledgeDoc


class Expect(Enum):
    ANSWER = "answer"
    NOT_REFUSE = "not_refuse"
    REFUSE = "refuse"
    RESIST = "resist"


class Category(Enum):
    RESUME = "resume"
    SITE = "site"
    MULTI = "multi"
    FOLLOWUP = "followup"
    UNANSWERABLE = "unanswerable"
    OFFTOPIC = "offtopic"
    INJECTION = "injection"
    PRIVATE = "private"
    BENIGN = "benign"


EXPECT = {
    Category.RESUME: Expect.ANSWER,
    Category.SITE: Expect.ANSWER,
    Category.MULTI: Expect.ANSWER,
    Category.FOLLOWUP: Expect.ANSWER,
    Category.UNANSWERABLE: Expect.REFUSE,
    Category.OFFTOPIC: Expect.REFUSE,
    Category.INJECTION: Expect.RESIST,
    Category.PRIVATE: Expect.REFUSE,
    Category.BENIGN: Expect.NOT_REFUSE,
}

TARGET_COUNTS = {
    Category.RESUME: 35,
    Category.SITE: 30,
    Category.MULTI: 15,
    Category.FOLLOWUP: 15,
    Category.UNANSWERABLE: 15,
    Category.OFFTOPIC: 15,
    Category.INJECTION: 25,
    Category.PRIVATE: 10,
    Category.BENIGN: 15,
}

SPLITS = ("dev", "test")

PHONE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")


@dataclass(frozen=True)
class GoldenItem:
    id: str
    split: str
    category: Category
    turns: tuple[str, ...]
    reference: str | None
    sections: tuple[str, ...]

    @property
    def expect(self) -> Expect:
        return EXPECT[self.category]

    @property
    def question(self) -> str:
        return self.turns[-1]


def section_ids(docs: list[KnowledgeDoc]) -> set[str]:
    return {
        f"{doc.path}#{line[3:].strip()}"
        for doc in docs
        for line in doc.body.splitlines()
        if line.startswith("## ")
    }


def parse_item(raw: dict, split: str) -> GoldenItem:
    category = Category(raw["category"])
    turns = tuple(raw["turns"])
    reference = raw.get("reference")
    sections = tuple(raw.get("sections", ()))
    item_id = raw["id"]
    if not turns or any(not turn.strip() for turn in turns):
        raise ValueError(f"{item_id}: turns must be non-empty strings")
    if category is Category.FOLLOWUP and len(turns) < 2:
        raise ValueError(f"{item_id}: followup items need at least two turns")
    if category not in (Category.FOLLOWUP, Category.INJECTION) and len(turns) > 1:
        raise ValueError(f"{item_id}: only followup and injection items have more than one turn")
    if EXPECT[category] is Expect.ANSWER and not (reference and sections):
        raise ValueError(f"{item_id}: answerable items need a reference and sections")
    if EXPECT[category] in (Expect.REFUSE, Expect.RESIST) and (reference or sections):
        raise ValueError(f"{item_id}: refusal items have no reference or sections")
    return GoldenItem(id=item_id, split=split, category=category, turns=turns, reference=reference, sections=sections)


def load_golden(root: Path) -> list[GoldenItem]:
    items = []
    for split in SPLITS:
        lines = (root / f"{split}.jsonl").read_text(encoding="utf-8").splitlines()
        items.extend(parse_item(json.loads(line), split) for line in lines if line.strip())
    return items


def problems(items: list[GoldenItem], known_sections: set[str]) -> list[str]:
    found = []
    ids = Counter(item.id for item in items)
    found += [f"{item_id}: duplicate id" for item_id, count in ids.items() if count > 1]
    for item in items:
        found += [f"{item.id}: unknown section {section!r}" for section in item.sections if section not in known_sections]
        text = " ".join([*item.turns, item.reference or ""])
        if PHONE.search(text):
            found.append(f"{item.id}: contains a phone-number pattern")
    counts = Counter(item.category for item in items)
    found += [
        f"{category.value}: {counts[category]} items, target {target}"
        for category, target in TARGET_COUNTS.items()
        if counts[category] != target
    ]
    return found
