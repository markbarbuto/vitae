import re
import time
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from enum import StrEnum

from vitae.output import OutputGuard
from vitae.prompt import NO_ANSWER, user_message
from vitae.retrieval import Retriever, query_for
from vitae.smalltalk import is_small_talk

MAX_CHARS = 500
INVISIBLE = re.compile(r"[​-‏⁠-⁤﻿\U000e0000-\U000e007f]")
SAMPLING = {
    "temperature": 0.3,
    "top_p": 0.9,
    "max_tokens": 220,
    "stop": [NO_ANSWER],
    "chat_template_kwargs": {"enable_thinking": False},
}


class Reason(StrEnum):
    NO_EVIDENCE = "no_evidence"
    NO_ANSWER = "no_answer"
    OUTPUT_BLOCKED = "output_blocked"


@dataclass(frozen=True)
class Meta:
    topics: tuple[str, ...]
    sources: tuple[str, ...]


@dataclass(frozen=True)
class Token:
    text: str


@dataclass(frozen=True)
class Refusal:
    reason: Reason
    text: str


@dataclass(frozen=True)
class Done:
    timings: dict[str, float] = field(default_factory=dict)


Event = Meta | Token | Refusal | Done


def normalize(text: str) -> str:
    text = INVISIBLE.sub("", unicodedata.normalize("NFKC", text))
    return " ".join(text.split())[:MAX_CHARS]


@dataclass
class Pipeline:
    retriever: Retriever
    aliases: dict[str, str]
    sources_of: dict[str, tuple[str, ...]]
    system: str
    generate: Callable[[list[dict]], Iterator[str]]
    refuse_below: float
    refusal_text: str
    small_talk_text: str
    hints: int = 3

    def answer(self, question: str, history: tuple[str, ...] = ()) -> Iterator[Event]:
        start = time.perf_counter()
        turns = tuple(normalize(turn) for turn in (*history[-1:], question))
        if is_small_talk(turns[-1]):
            yield Meta((), ())
            yield Token(self.small_talk_text)
            yield Done({"total_ms": _ms(start)})
            return

        retrieval = self.retriever.search(query_for(turns, self.aliases), self.refuse_below)
        retrieved = _ms(start)
        if retrieval.refused(self.refuse_below):
            yield Meta((), ())
            yield Refusal(Reason.NO_EVIDENCE, self.refusal_text)
            yield Done({"retrieval_ms": retrieved, "relevance": retrieval.relevance, "total_ms": _ms(start)})
            return

        topics = tuple(hit.topic for hit in retrieval.hits[:3])
        yield Meta(topics, tuple(source for topic in topics for source in self.sources_of[topic]))
        hints = topics[: self.hints]
        messages = [{"role": "system", "content": self.system}, {"role": "user", "content": user_message(turns, hints)}]
        guard, first = OutputGuard(), None
        for delta in self.generate(messages):
            first = first or _ms(start)
            if text := guard.feed(delta):
                yield Token(text)
            if guard.blocked or guard.declined:
                break
        timings = {"retrieval_ms": retrieved, "first_token_ms": first or _ms(start), "relevance": retrieval.relevance}
        tail = guard.finish()
        if guard.blocked:
            yield Refusal(Reason.OUTPUT_BLOCKED, self.refusal_text)
        elif guard.declined or not guard.text:
            yield Refusal(Reason.NO_ANSWER, self.refusal_text)
        elif tail:
            yield Token(tail)
        yield Done({**timings, "total_ms": _ms(start)})


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)
