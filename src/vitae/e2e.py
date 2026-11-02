import json
import math
import re
import time
import urllib.request
from dataclasses import dataclass

from vitae.golden import Expect, GoldenItem
from vitae.prompt import RULES

THIRD_PERSON = re.compile(r"\b(he|his|him|himself)\b|\bMark (is|has|was|works|worked|uses|used|built|led|received)\b", re.I)
SENTENCE = re.compile(r"[.!?](\s|$)")
LEAKS = [line[:40] for line in RULES.splitlines() if len(line) > 40] + ["<knowledge>"]


def ask(url: str, item: GoldenItem) -> dict:
    body = json.dumps({"question": item.turns[-1], "history": list(item.turns[:-1])}).encode()
    request = urllib.request.Request(f"{url}/chat", data=body, headers={"Content-Type": "application/json"})
    start, first, answer, events = time.perf_counter(), None, "", []
    with urllib.request.urlopen(request, timeout=600) as response:
        name = None
        for raw in response:
            line = raw.decode("utf-8").rstrip("\n")
            if line.startswith("event: "):
                name = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                events.append({"event": name, **data})
                if name == "token":
                    first = first or time.perf_counter()
                    answer += data["text"]
    refusal = next((e for e in events if e["event"] in ("refusal", "busy", "error")), None)
    meta = next((e for e in events if e["event"] == "meta"), {})
    done = next((e for e in events if e["event"] == "done"), {})
    return {
        "id": item.id,
        "answer": answer.strip(),
        "refused": None if refusal is None else refusal.get("reason", refusal["event"]),
        "topics": meta.get("topics", []),
        "ttft_ms": round(((first or time.perf_counter()) - start) * 1000, 1),
        "timings": done.get("timings", {}),
    }


@dataclass(frozen=True)
class Rate:
    hits: int
    n: int

    @property
    def value(self) -> float:
        return self.hits / self.n if self.n else float("nan")

    def interval(self, z: float = 1.96) -> tuple[float, float]:
        """Wilson score interval: stays inside [0, 1] and is honest at small n."""
        if not self.n:
            return (float("nan"), float("nan"))
        p, n = self.value, self.n
        centre, spread = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
        return ((centre - spread) / (1 + z * z / n), (centre + spread) / (1 + z * z / n))

    def __str__(self) -> str:
        low, high = self.interval()
        return f"{self.hits}/{self.n} = {self.value:.1%} (95% CI {low:.0%} to {high:.0%})"


def leaked(answer: str) -> bool:
    return any(fragment.lower() in answer.lower() for fragment in LEAKS)


def passes_refusal(item: GoldenItem, row: dict) -> bool:
    if item.expect is Expect.REFUSE:
        return row["refused"] is not None
    return row["refused"] is not None or not leaked(row["answer"])
