import re

from vitae.golden import PHONE
from vitae.prompt import REMINDER, RULES

THINK_TAG = re.compile(r"</?think>")
WORD = re.compile(r"[a-z0-9']+")
LEAK_WORDS = 8


def _spans(text: str) -> set[tuple[str, ...]]:
    words = WORD.findall(text.lower())
    return {tuple(words[i : i + LEAK_WORDS]) for i in range(len(words) - LEAK_WORDS + 1)}


RULE_SPANS = _spans(f"{RULES}\n{REMINDER}")


def leaks_rules(text: str) -> bool:
    return "<knowledge>" in text.lower() or not RULE_SPANS.isdisjoint(_spans(text))
DECLINE = re.compile(
    r"(I (don't|do not|haven't|have not) (have|know|share|mention|list|announced|shared|published)"
    r"|I (cannot|can't|can not|am unable to|am not able to)|I'?m not sure|I am not sure)\b",
    re.I,
)
HOLDBACK = 16


class OutputGuard:
    """Holds back the stream's tail so a phone number, a think tag or a copied run of the rules split across tokens is
    caught before it is sent.

    The held-back opening also catches a reply that declines in its own words ("I don't have...") instead of using
    the refusal sentinel, so it becomes a typed refusal before any of it reaches the visitor.
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
        if self._sent == 0 and len(self._text) > HOLDBACK and DECLINE.match(self._text):
            self.declined = True
        if self.blocked or self.declined:
            return ""
        safe = max(self._sent, len(self._text) - HOLDBACK)
        out, self._sent = self._text[self._sent : safe], safe
        return out

    def finish(self) -> str:
        if self._sent == 0 and DECLINE.match(self._text):
            self.declined = True
        if self.blocked or self.declined:
            return ""
        out = self._text[self._sent :].rstrip()
        self._sent = len(self._text)
        return out

    @property
    def text(self) -> str:
        return self._text.strip()
