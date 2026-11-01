import re
from dataclasses import dataclass

from vitae.golden import Category, GoldenItem

QUOTAS = {Category.RESUME: 12, Category.SITE: 10, Category.MULTI: 7, Category.FOLLOWUP: 7, Category.BENIGN: 4}

SHEET_HEADER = """# Calibration labels

Label each answer by hand, without looking at the judge's output. Write `y` or `n` after each label.

- **correct**: the answer responds to the question, and its main facts agree with the reference. Extra true details are fine. Leaving out a minor detail is fine.
- **faithful**: every fact the answer states about you is true according to your knowledge base. One wrong employer, date, number or invented detail makes it `n`, even if the main answer is right.

Use `note` for anything worth discussing. Then run `uv run assistant calibrate score`.
"""

LABEL = re.compile(r"^- (correct|faithful|note):[ \t]*(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class Label:
    item_id: str
    correct: bool
    faithful: bool
    note: str


def sample(items: list[GoldenItem]) -> list[GoldenItem]:
    chosen = []
    for category, quota in QUOTAS.items():
        pool = [item for item in items if item.split == "dev" and item.category is category and item.reference]
        chosen += [pool[index * len(pool) // quota] for index in range(quota)]
    return chosen


def render_sheet(entries: list[tuple[GoldenItem, str]]) -> str:
    blocks = [SHEET_HEADER]
    for item, answer in entries:
        previous = f"**Previous question:** {item.turns[-2]}\n\n" if len(item.turns) > 1 else ""
        blocks.append(
            f"## {item.id}\n\n{previous}**Question:** {item.question}\n\n**Reference:** {item.reference}\n\n"
            f"**Answer:** {answer}\n\n- correct: \n- faithful: \n- note: \n"
        )
    return "\n".join(blocks)


def _yes_no(value: str, item_id: str, field: str) -> bool:
    value = value.strip().lower()
    if value not in ("y", "n"):
        raise ValueError(f"{item_id}: {field} must be y or n, got {value!r}")
    return value == "y"


def parse_sheet(text: str) -> list[Label]:
    labels = []
    for block in text.replace("\r\n", "\n").split("\n## ")[1:]:
        item_id = block.splitlines()[0].strip()
        fields = dict(LABEL.findall(block))
        labels.append(
            Label(
                item_id=item_id,
                correct=_yes_no(fields.get("correct", ""), item_id, "correct"),
                faithful=_yes_no(fields.get("faithful", ""), item_id, "faithful"),
                note=fields.get("note", "").strip(),
            )
        )
    return labels


@dataclass(frozen=True)
class Agreement:
    n: int
    agree: int
    kappa: float

    @property
    def rate(self) -> float:
        return self.agree / self.n


def agreement(human: list[bool], judge: list[bool]) -> Agreement:
    n = len(human)
    agree = sum(h == j for h, j in zip(human, judge, strict=True))
    p_human, p_judge = sum(human) / n, sum(judge) / n
    expected = p_human * p_judge + (1 - p_human) * (1 - p_judge)
    kappa = 1.0 if expected == 1 else (agree / n - expected) / (1 - expected)
    return Agreement(n=n, agree=agree, kappa=kappa)
