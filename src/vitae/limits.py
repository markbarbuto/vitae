import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

MINUTE, DAY = 60.0, 86400.0


@dataclass(frozen=True)
class Window:
    seconds: float
    limit: int


PER_VISITOR = (Window(MINUTE, 4), Window(DAY, 30))
GLOBAL = Window(DAY, 300)


@dataclass
class RateLimiter:
    """Rolling-window limits per visitor IP, plus one global daily cap. The process is the only writer, so the hits
    live in memory and reset on restart."""

    clock: Callable[[], float] = time.monotonic
    visitors: dict[str, deque[float]] = field(default_factory=dict)
    everyone: deque[float] = field(default_factory=deque)

    def check(self, ip: str) -> float | None:
        """Record a hit and return None, or return the seconds until the visitor may ask again without recording it."""
        now = self.clock()
        hits = self.visitors.setdefault(ip, deque())
        while hits and hits[0] <= now - DAY:
            hits.popleft()
        while self.everyone and self.everyone[0] <= now - DAY:
            self.everyone.popleft()
        waits = [_wait(hits, window, now) for window in PER_VISITOR] + [_wait(self.everyone, GLOBAL, now)]
        wait = max((w for w in waits if w is not None), default=None)
        if wait is None:
            hits.append(now)
            self.everyone.append(now)
        elif not hits:
            del self.visitors[ip]
        return wait


def _wait(hits: deque[float], window: Window, now: float) -> float | None:
    inside = [t for t in hits if t > now - window.seconds]
    if len(inside) < window.limit:
        return None
    return round(inside[-window.limit] + window.seconds - now, 1)
