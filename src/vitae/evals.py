from dataclasses import dataclass

from vitae.golden import Category, GoldenItem
from vitae.retrieval import Retrieval

RECALL_K = 4


@dataclass(frozen=True)
class Ranked:
    item: GoldenItem
    gold: frozenset[str]
    retrieval: Retrieval

    @property
    def topics(self) -> list[str]:
        return [hit.topic for hit in self.retrieval.hits]

    def recall(self, k: int = RECALL_K) -> float:
        return len(self.gold & set(self.topics[:k])) / min(len(self.gold), k)

    @property
    def reciprocal_rank(self) -> float:
        ranks = [rank for rank, topic in enumerate(self.topics, 1) if topic in self.gold]
        return 1 / ranks[0] if ranks else 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


def refusal_rates(results: list[Ranked], refuse_below: float) -> dict[Category, float]:
    rates = {}
    for category in Category:
        group = [result for result in results if result.item.category is category]
        if group:
            rates[category] = mean([result.retrieval.refused(refuse_below) for result in group])
    return rates
