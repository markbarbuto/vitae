import re
from itertools import product

from vitae.golden import PHONE
from vitae.prompt import REMINDER, RULES

THINK_TAG = re.compile(r"</?think>")
WORD = re.compile(r"[a-z0-9']+")
LEAK_WORDS = 8
# Text at the end of the stream that could still grow into a phone number or a think tag.
UNSAFE_TAIL = re.compile(r"([\d(][\d\s().-]*|<[/a-z]*)$")
DECLINES = tuple(
    f"i {negation} {verb}"
    for negation, verb in product(
        ("don't", "do not", "haven't", "have not"), ("have", "know", "share", "mention", "list", "announced", "shared", "published")
    )
) + ("i cannot", "i can't", "i can not", "i am unable to", "i am not able to", "i'm not sure", "im not sure", "i am not sure")


def _spans(text: str) -> set[tuple[str, ...]]:
    words = WORD.findall(text.lower())
    return {tuple(words[i : i + LEAK_WORDS]) for i in range(len(words) - LEAK_WORDS + 1)}


RULE_SPANS = _spans(f"{RULES}\n{REMINDER}")


def leaks_rules(text: str) -> bool:
    return "<knowledge>" in text.lower() or not RULE_SPANS.isdisjoint(_spans(text))


def _opening(text: str) -> str:
    """'decline' if the reply opens with a decline phrase, 'open' while it still could, else 'answer'."""
    lowered = text.lower().replace("’", "'")
    for phrase in DECLINES:
        if lowered.startswith(phrase) and not lowered[len(phrase) : len(phrase) + 1].isalnum():
            return "decline"
    return "open" if any(phrase.startswith(lowered) or lowered.startswith(phrase) for phrase in DECLINES) else "answer"


class OutputGuard:
    """Sends text as soon as nothing after it can turn it into a phone number, a think tag or a decline.

    Only a trailing run that could still grow into a phone number or tag is held back, and only an opening that
    could still become a decline ("I don't have...", "I cannot"). A reply that declines in its own words becomes a
    typed refusal before any of it reaches the visitor. A copied run of the rules is blocked within 8 words.
    """

    def __init__(self) -> None:
        self._text = ""
        self._sent = 0
        self.blocked = False
        self.declined = False

    def feed(self, delta: str) -> str:
        self._text = THINK_TAG.sub("", self._text + delta)
        if self._sent == 0:
            self._text = self._text.lstrip()
        if PHONE.search(self._text) or leaks_rules(self._text):
            self.blocked = True
        if self._sent == 0:
            opening = _opening(self._text)
            self.declined = opening == "decline"
            if opening == "open":
                return ""
        if self.blocked or self.declined:
            return ""
        tail = UNSAFE_TAIL.search(self._text)
        safe = max(self._sent, tail.start() if tail else len(self._text))
        out, self._sent = self._text[self._sent : safe], safe
        return out

    def finish(self) -> str:
        if self._sent == 0 and _opening(self._text.strip()) == "decline":
            self.declined = True
        if self.blocked or self.declined:
            return ""
        out = self._text[self._sent :].rstrip()
        self._sent = len(self._text)
        return out

    @property
    def text(self) -> str:
        return self._text.strip()
